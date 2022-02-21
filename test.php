<?php // Author: Patrik Skaloš


ini_set('display_errors', 'stderr');


/*
 * Constants
 */


// Usage reply
define("USAGE", 
"Brief:
  This script tests your parser of language IPPcode22 written in PHP and/or 
  your interpret written in python against your test cases. After testing, it
  generates a test report in HTML to the standard output.

Usage: 
  php8.1 test.php [--help] [--directory=path] [--recursive] 
      [--parse-script=file] [--int-script=file] [--parse-only] [--int-only] 
      [--jexampath=path] [--noclean]

Options:
  --help: displays this menu
  --directory=path: searches for the test cases in directory 'path'
  --recursive: searches for the test cases recursively (including 
      subdirectories)
  --parse-script=file: path to the parser PHP file. If not provided, 
      ./parse.php will be used
  --int-script=file: path to the interpret python file. If not provided, 
      ./interpret.py will be used
  --parse-only: only the parser will be tested. Do not use along with 
      --int-only or --int-script
  --int-only: only the interpret will be tested. Do not use along with 
      --parse-only, --parse-script or --jexampath
  --jexampath=path: path to the directory where files 'jexamxml.jar' and 
      'options' can be found. If not provided, path /pub/courses/ipp/jexamxml/ 
      will be used
  --noclean: does not remove the temporary files after tests are done
");

// File extensions
define("TEST_EXTENSION", ".src");
define("IN_EXTENSION", ".in");
define("OUT_EXTENSION", ".out");
define("RC_EXTENSION", ".rc");

// User options
define("OPTIONS", [
  "help",
  "directory:",
  "recursive",
  "parse-script::",
  "int-script::",
  "parse-only",
  "int-only",
  "jexampath:",
  "noclean"
]);


/*
 * Classes
 */


// TODO refactor
class TestCase{
  public $dir;
  public $name;

  public $paths;
  public $contents;
  public $output_paths;
  public $returned_code;

  public $success;

  // Gets all the test-case data to be ready to execute the test
  function __construct($dir, $filename){
    $this->name = $filename;
    $this->dir = $dir;

    // Generate other files' paths
    $this->paths = [
      "test" => $this->dir . $this->name,
      "in" => str_replace(TEST_EXTENSION, IN_EXTENSION, $this->dir . $this->name),
      "out" => str_replace(TEST_EXTENSION, OUT_EXTENSION, $this->dir . $this->name),
      "rc" => str_replace(TEST_EXTENSION, RC_EXTENSION, $this->dir . $this->name)
    ];

    $this->output_paths = [
      "stdout" => str_replace(TEST_EXTENSION, ".out_tmp", $this->dir . $this->name),
      "stderr" => str_replace(TEST_EXTENSION, ".err_tmp", $this->dir . $this->name),
      "diff" => str_replace(TEST_EXTENSION, ".xml", $this->dir . $this->name),
    ];

    // Write 0 to return code file if the file does not exist
    if(!file_exists($this->paths["rc"])){
      if(!file_put_contents($this->paths["rc"], "0")){
        // TODO err
      }
    }
    // Create all other files if they don't exist
    foreach(array_merge($this->paths, $this->output_paths) as $path){
      if(!touch($path)){
        // TODO err
      }
    }

    // Read from those files
    foreach($this->paths as $key => $path){
      $file = fopen($path, "r");
      if(!$file){
        // TODO err
      }
      $this->contents[$key] = file_get_contents($path);
      if($this->contents[$key] == False){
        // TODO err
      }

      fclose($file);
    }

    // print("Test case initialized: " . $this->dir . $this->name . "\n");
    // TODO
  }

  // Execute the script with the inputs provided
  function execute($script_path){
    $command = "php8.1 " 
        . "\"" . $script_path . "\""
        . " < \"" . $this->paths["test"] . "\""
        . " > \"" . $this->output_paths["stdout"] . "\""
        . " 2> \"" . $this->output_paths["stderr"] . "\"";
    exec($command, $dummy, $ret_val);
    $this->returned_code = $ret_val;
    // print("Test case ran: " . $this->dir . $this->name . "\n");
    // TODO
  }

  // Check the output with the reference files
  function evaluate($jexamxml_dir){
    // If the returned code is not zero, just check if it matches the reference
    if($this->returned_code != 0){
      if($this->returned_code == file_get_contents($this->paths["rc"])){
        $this->success = True;
      }else{
        $this->success = False;
      }
    }else{
      $command = "java -jar "
        . "\"" . $jexamxml_dir . "jexamxml.jar\" "
        . "\"" . $this->paths["out"] . "\" "
        . "\"" . $this->output_paths["stdout"] . "\" "
        . "\"" . $this->output_paths["diff"] . "\" "
        . "\"/D\" "
        . "\"" . $jexamxml_dir . "options" . "\" ";
      exec($command, $dummy, $ret_val);

      // Check the diff, stderr and return code
      if($ret_val == 0 
          && filesize($this->output_paths["stderr"]) == 0
          && $this->returned_code == file_get_contents($this->paths["rc"])){
        $this->success = True;
      }else{
        $this->success = False;
      }
    }
  }

  // Show evaluation:
  function printEvaluation(){
    if(!$this->success){
      print("\n");
      print("<div style=\"border: 5x solid red; border-radius: 10px; margin: 25px; padding: 10px; width: calc(100\% - 50px); background-color: #2e0000;\">\n");
      print("FAILED: " . $this->dir . $this->name . "<br>\n");
      print("==================================================<br>\n");
      
      print("TEST:\n" . file_get_contents($this->paths["test"]) . "<br>\n");
      print("==================================================<br>\n");

      if($this->returned_code != file_get_contents($this->paths["rc"])){
        // Didn't pass because of wrong return code
        print("RETURN CODE:<br>\n");
        print("Expected: " . file_get_contents($this->paths["rc"]) . "<br>\n");
        print("Received: " . $this->returned_code . "<br>\n");
        print("==================================================<br>\n");
        print("STDERR:<br>\n");
        print(file_get_contents($this->output_paths["stderr"]));
        print("<br>\n");
      }else{
        print("STDERR:<br>\n");
        print(file_get_contents($this->output_paths["stderr"]));
        print("<br>\n");
        print("==================================================<br>\n");
        print("EXPECTED:<br>\n");
        print(file_get_contents($this->paths["out"]));
        print("==================================================<br>\n");
        print("RECEIVED:<br>\n");
        print(file_get_contents($this->output_paths["stdout"]));
        print("==================================================<br>\n");
        print("DIFF:<br>\n");
        print(file_get_contents($this->output_paths["diff"]));
      }
      print("</div>\n\n");
    }
  }

  // Remove all temporary files of this test case
  function clean(){
    foreach($this->output_paths as $file){
      if(file_exists($file)){
        unlink($file);
      }
    }
    if(file_exists(str_replace(TEST_EXTENSION, ".out.log", $this->dir . $this->name))){
      unlink(str_replace(TEST_EXTENSION, ".out.log", $this->dir . $this->name));
    }
  }
}


// Fetches all files ending with .src in $dir. Also searches subdirectories
// recursively if $recursive == True
// Returns an array of which elements are objects of class TestCase
function getTestCasesInDir($dir, $recursive){
  $test_cases = [];
  $content = scandir($dir);

  // Get all src files
  for($i = 0; $i < count($content); $i++){
    if(!is_dir($dir . $content[$i]) 
        && str_ends_with($content[$i], TEST_EXTENSION)){
      array_push($test_cases, new TestCase($dir, $content[$i]));
    }
  }
  
  // Recursively get files from all subdirectories
  if($recursive){
    for($i = 0; $i < count($content); $i++){
      if(is_dir($dir . $content[$i]) 
          && !str_starts_with($content[$i], '.')){
        $test_cases = array_merge(
          $test_cases, 
          getTestCasesInDir($dir . $content[$i] . '/', $recursive)
        );
      }
    }
  }

  return $test_cases;
}


/*
 *
 * Main program flow
 *
 */


// Get all options and if some of them are conflicted or canot parse -> err
$options = getopt("", OPTIONS);
if($options == False
    || (array_key_exists("parse-only", $options) && array_key_exists("int-only", $options))
    || (array_key_exists("parse-script", $options) && array_key_exists("int-only", $options))
    || (array_key_exists("int-script", $options) && array_key_exists("parse-only", $options))){
  trigger_error("Failed to parse the arguments provided by the user", E_USER_ERROR);
  exit(10);
}

if(array_key_exists("help", $options)){
  print(USAGE);
  exit(0);
}

// Get tests directory
if(array_key_exists("directory", $options)){
  $tests_dir = $options["directory"];
  if(!str_ends_with($tests_dir, '/')){
    $tests_dir = $tests_dir . '/';
  }
}else{
  $tests_dir = "./";
}

// Get the recursive option
$recursive = array_key_exists("recursive", $options);

if(array_key_exists("parse-script", $options)){
  $parser = $options["parse-script"];
}else{
  $parser = "./parse.php";
}

if(array_key_exists("int-script", $options)){
  $interpret = $options["int-script"];
}else{
  $interpret = "./interpret.py";
}

if(array_key_exists("parse-only", $options)){
  $action = "parse";
}else if(array_key_exists("int-only", $options)){
  $action = "int";
}else{
  $action = "both";
}

if(array_key_exists("jexampath", $options)){
  $jexamxml_dir = $options["jexampath"];
  if(!str_ends_with($jexamxml_dir, '/')){
    $jexamxml_dir = $jexamxml_dir . '/';
  }
}else{
  $jexamxml_dir = "/pub/courses/ipp/jexamxml/";
}

if(array_key_exists("noclean", $options)){
  $clean = False;
}else{
  $clean = True;
}


// Check if dirs and files exist
if(!file_exists($tests_dir)
    || (!file_exists($jexamxml_dir . "jexamxml.jar") && $action == "parse")
    || (!file_exists($jexamxml_dir . "options") && $action == "parse")
    || (!file_exists($parser) && $action != "int")
    || (!file_exists($interpret) && $action != "parse")){
  trigger_error("A path provided by the user does not exist", E_USER_ERROR);
  exit(41);
}


print("<!DOCTYPE html>\n");
print("<html>\n");
print("<head>\n");
print("<title>IPP project test results</title>\n");
print("</head>\n");
print("<body style=\"background-color: #111; color: #ddd;\">\n");


$test_cases = getTestCasesInDir($tests_dir, $recursive);
$total_tests = count($test_cases);
$result = ["passed" => 0, "total" => 0];

// Execute and evaluate the tests
foreach($test_cases as $test_case){

  // Execute the tests
  $test_case->execute($parser);

  // Evaluate the tests
  $test_case->evaluate($jexamxml_dir);

  // Calculate the result
  if($test_case->success){
    $result["passed"]++;
  }
  $result["total"]++;

}

// Print tests overview
print("<div style=\"text-align: center; margin: 50px; margin-bottom: 100px; border: 5px solid #22ff22aa;\">\n");
print("<p style=\"font-size: 4em;\">Overview</p>\n");
print("<p style=\"font-size: 2em; margin-bottom: 75px;\">\n");
if($result["passed"] != $result["total"]){
  print("Passed " . $result["passed"] . " out of " . $result["total"] . " tests\n");
}else{
  print("All " . $result["total"] . " tests passed! Congratulations!\n");
}
print("</p>\n");
print("</div>\n");

// Print information about the failed tests
if($result["passed"] != $result["total"]){
  print("<div>\n");
  print("<h1 style=\"text-align: center;\">Failed tests info:</h1>\n");
  foreach($test_cases as $test_case){
    $test_case->printEvaluation();
  }
  print("</div>\n");
}

// Remove the tmp files
if($clean){
  foreach($test_cases as $test_case){
    $test_case->clean();
  }
}

print("</body>\n");
print("</html>\n");

?>
