<?php // Author: Patrik Skaloš

// Warning: the standard output is to be forwarded to a HTML file and read by a
// browser


/*
 *
 * Constants
 *
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
define("TEST_EXT", ".src");
define("IN_EXT", ".in");
define("OUT_EXT", ".out");
define("RC_EXT", ".rc");


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
 *
 * Classes
 *
 */


/*
 * Test case class containing everything about a test:
 *
 * $dir: the directory where the test case is located
 * $name: name of the test case's source file (eg. abc.src)
 * $paths: object containing paths to .src (source code), .in (input), 
 *   .out (reference output), .rc (reference return code), .out_tmp (stdout), 
 *   .err_tmp (stderr) and .diff_tmp (difference between output and reference)
 * $returned_code: code returned by executing the test
 * $success: boolean, true if the test was successful
 */
class TestCase{
  public $dir;
  public $name;
  public $paths;
  public $returned_code;
  public $success;

  // Gets all the test-case data to be ready to execute the test
  function __construct($dir, $filename){
    $this->name = $filename;
    $this->dir = $dir;

    // Generate other files' paths
    $this->paths = [
      "test" => $this->dir . $this->name,
      "in" => str_replace(TEST_EXT, IN_EXT, $this->dir . $this->name),
      "out" => str_replace(TEST_EXT, OUT_EXT, $this->dir . $this->name),
      "rc" => str_replace(TEST_EXT, RC_EXT, $this->dir . $this->name),
      "stdout" => str_replace(TEST_EXT, ".out_tmp", $this->dir . $this->name),
      "stderr" => str_replace(TEST_EXT, ".err_tmp", $this->dir . $this->name),
      "diff" => str_replace(TEST_EXT, ".diff_tmp", $this->dir . $this->name),
    ];

    // Write 0 to return code file if the rc file does not exist
    if(!file_exists($this->paths["rc"])){
      if(!file_put_contents($this->paths["rc"], "0")){
        trigger_error("Cannot create temporary file:" . $this->paths["rc"], 
          E_USER_WARNING);
        exit(41);
      }
    }

    // Create all other files if they don't exist
    foreach(array_merge($this->paths, $this->paths) as $path){
      if(!touch($path)){
        trigger_error("Cannot create temporary file:" . $path, 
          E_USER_WARNING);
        exit(41);
      }
    }
  }


  // Execute the script with the inputs provided
  function execute($target, $parser_path, $int_path){

    // Test the parser aonly
    if($target == "parser"){
      $command = "php8.1 " 
          . "\"" . $parser_path . "\" "
          . "< \"" . $this->paths["test"] . "\" "
          . "> \"" . $this->paths["stdout"] . "\" "
          . "2> \"" . $this->paths["stderr"] . "\" ";

    // Test the interpret only
    }else if ($target == "interpret"){
      $command = "python3.8 "
          . "\"" . $int_path . "\" "
          . "--source=\"" . $this->paths["test"] . "\" "
          . "--input=\"" . $this->paths["in"] . "\" "
          . "> \"" . $this->paths["stdout"] . "\" "
          . "2> \"" . $this->paths["stderr"] . "\" ";

    // Test both of them by running the parser and forwarding stdout to int
    }else{
      $command = "php8.1 " 
          . "\"" . $parser_path . "\" "
          . "< \"" . $this->paths["test"] . "\" "
          . "2> \"" . $this->paths["stderr"] . "\" "
          . "| python3 "
          . "\"" . $int_path . "\" "
          . "--input=\"" . $this->paths["in"] . "\" "
          . "> \"" . $this->paths["stdout"] . "\" "
          . "2> \"" . $this->paths["stderr"] . "\" ";
    }

    // Execute the command, keep the return code
    exec($command, $dummy, $this->returned_code);
  }


  // Check the output with the reference files
  function evaluate($target, $jexamxml_dir){

    // If the returned code is not 0, just check if it matches the reference
    if($this->returned_code != 0){
      if($this->returned_code == file_get_contents($this->paths["rc"])){
        $this->success = True;
      }else{
        $this->success = False;
      }

    // Else, check the differences between outputs
    }else{

      // Evaluate the parser output
      if($target == "parser"){
        $command = "java -jar "
          . "\"" . $jexamxml_dir . "jexamxml.jar\" "
          . "\"" . $this->paths["out"] . "\" "
          . "\"" . $this->paths["stdout"] . "\" "
          . "\"" . $this->paths["diff"] . "\" "
          . "\"/D\" "
          . "\"" . $jexamxml_dir . "options" . "\" ";

      // Evaluate the interpret output or both outputs
      }else{
        $command = "diff -qyt --left-column "
          . "\"" . $this->paths["out"] . "\" "
          . "\"" . $this->paths["stdout"] . "\" ";
      }

      // Execute the evaluation command
      exec($command, $dummy, $diff_ret_val);

      // Check the diff and return code (I guess I don't need to check if
      // stderr is empty)
      if($this->returned_code == file_get_contents($this->paths["rc"])
          && $diff_ret_val == 0){
        $this->success = True;
      }else{
        $this->success = False;
      }
    }
  }


  // Print evaluation as HTML:
  function printEvaluation(){

    // If the test failed, print comprehensive information about it
    if(!$this->success){

      // Create a DIV with dark red background
      print("<div style=\"border: 5x solid red; border-radius: 10px; "
        . "margin: 25px; padding: 10px; width: calc(100\% - 50px); "
        . "background-color: #2e0000;\">\n");

      // Print the test path and contents
      print("FAILED: " . $this->dir . $this->name . "\n");
      print("<hr>");
      print("CODE INPUT:\n");
      print(html_string(file_get_contents($this->paths["test"])) . "\n");
      print("<hr>");

      // Didn't pass because of different return codes? Print them
      if($this->returned_code != file_get_contents($this->paths["rc"])){
        print("RETURN CODE:<br>\n");
        print("Expected: " . file_get_contents($this->paths["rc"]) . "<br>\n");
        print("Received: " . $this->returned_code . "<br>\n");

      // Didn't pass because the output is wrong? Print them
      }else{
        print("EXPECTED OUTPUT:\n");
        print(html_string(file_get_contents($this->paths["out"])) . "\n");
        print("<hr>");
        print("RECEIVED OUTPUT:\n");
        print(html_string(file_get_contents($this->paths["stdout"])) . "\n");
      }

      // Print stderr in either case
      print("<hr>");
      print("STDERR:\n");
      print(html_string(file_get_contents($this->paths["stderr"])) . "\n");

    // If a test passed, only print the path and code input
    }else{

      // Create a DIV with dark green background
      print("<div style=\"border: 5x solid red; border-radius: 10px; "
        . "margin: 25px; padding: 10px; width: calc(100\% - 50px); "
        . "background-color: #002e00;\">\n");

      // Print the path and the code input
      print("PASSED: " . $this->dir . $this->name . "\n");
      print("<hr>");
      print("CODE INPUT:\n");
      print(html_string(file_get_contents($this->paths["test"])) . "\n");
    }
    print("</div>\n\n");
  }


  // Remove all temporary files of this test case
  function clean(){
    $to_clean = [
      $this->paths["stdout"],
      $this->paths["stderr"],
      $this->paths["diff"], 
      str_replace(TEST_EXT, ".out.log", $this->dir . $this->name),
    ];
    foreach($to_clean as $file){
      if(file_exists($file)){
        unlink($file);
      }
    }
  }
}

/*
 *
 * Functions
 *
 */


// Fetches all files ending with .src in $dir. Also searches subdirectories
// recursively if $recursive == True
// Returns an array of which elements are objects of class TestCase
function getTestCasesInDir($dir, $recursive){
  $test_cases = [];

  // Get all contents in the directory (files and directories)
  $content = scandir($dir);

  // Get all src files
  for($i = 0; $i < count($content); $i++){
    if(!is_dir($dir . $content[$i]) 
        && str_ends_with($content[$i], TEST_EXT)){
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


// Create a <pre> element to format the code and convert special characters
// (eg. &) to html friendly ones (eg. &amp)
function html_string($str){
  return "<pre style=\"margin: 0;\">" 
    . htmlspecialchars($str, ENT_QUOTES) 
    . "</pre>";
}


/*
 *
 * Main program flow
 *
 */


ini_set('display_errors', 'stderr');

/*
 * Get and parse the user options
 */

// Get all options, if some of them are conflicted or canot parse -> err
$options = getopt("", OPTIONS);
if($options == False
    || ( array_key_exists("parse-only", $options) 
      && array_key_exists("int-only", $options))
    || ( array_key_exists("parse-script", $options) 
      && array_key_exists("int-only", $options))
    || ( array_key_exists("int-script", $options) 
      && array_key_exists("parse-only", $options))){
  trigger_error("Failed to parse the arguments provided by the user", 
    E_USER_WARNING);
  exit(10);
}

// Print usage if asked
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

// Get parser path
if(array_key_exists("parse-script", $options)){
  $parser = $options["parse-script"];
}else{
  $parser = "./parse.php";
}

// Get interpret path
if(array_key_exists("int-script", $options)){
  $interpret = $options["int-script"];
}else{
  $interpret = "./interpret.py";
}

// Get the jexamxml directory path
if(array_key_exists("jexampath", $options)){
  $jexamxml_dir = $options["jexampath"];
  if(!str_ends_with($jexamxml_dir, '/')){
    $jexamxml_dir = $jexamxml_dir . '/';
  }
}else{
  $jexamxml_dir = "/pub/courses/ipp/jexamxml/";
}

// Get the test target
if(array_key_exists("parse-only", $options)){
  $target = "parser";
}else if(array_key_exists("int-only", $options)){
  $target = "interpret";
}else{
  $target = "both";
}

// Get the recursive option
$recursive = array_key_exists("recursive", $options);

// Check if dirs and files exist
if(!file_exists($tests_dir)
    || ($target == "parser"    && !file_exists($jexamxml_dir . "jexamxml.jar"))
    || ($target == "parser"    && !file_exists($jexamxml_dir . "options"))
    || ($target != "interpret" && !file_exists($parser))
    || ($target != "parser"    && !file_exists($interpret))){
  trigger_error("One of the paths provided does not exist", E_USER_WARNING);
  exit(41);
}

/*
 * Execute the tests and print the report to the standard output as HTML
 */

// Print the report beginning
print("<!DOCTYPE html>\n");
print("<html>\n");
print("<head>\n");
print("<title>IPP project test results</title>\n");
print("</head>\n");
print("<body style=\"background-color: #111; color: #ddd;\">\n");

// Get test cases, count them and initialize the results object
$test_cases = getTestCasesInDir($tests_dir, $recursive);
$total_tests = count($test_cases);
$results = ["passed" => 0, "total" => 0];

// Execute and evaluate the tests
foreach($test_cases as $test_case){

  // Execute the tests
  $test_case->execute($target, $parser, $interpret);

  // Evaluate the tests
  $test_case->evaluate($target, $jexamxml_dir);

  // Update the results object
  if($test_case->success){
    $results["passed"]++;
  }
  $results["total"]++;

  // TODO remove?
  // Print an overwriting line showing the testing status
  fwrite(STDERR, $results["passed"] . "/" . $results["total"] 
    . " tests passed. Total tests: " . $total_tests . "\r");
}

// Clear the overwriting line
fwrite(STDERR, "                                                           \r");

// Print tests overview
print("<div style=\"text-align: center; margin: 50px; margin-bottom: 100px; "
  . "border: 5px solid #22ff22aa;\">\n");
print("<p style=\"font-size: 3em;\">Tests overview for: " . $target . "</p>\n");
print("<p style=\"font-size: 2em; margin-bottom: 50px;\">\n");
if($results["passed"] != $results["total"]){
  print($results["passed"] . " of " . $results["total"] . " tests passed\n");
}else{
  print("All " . $results["total"] . " tests passed! Congratulations!\n");
}
print("</p>\n");
print("</div>\n");

// Print information about the failed tests
if($results["passed"] != $results["total"]){
  foreach($test_cases as $test_case){
    if(!$test_case->success){
      $test_case->printEvaluation();
    }
  }
}

// Print all tests that passed (below the failed ones)
foreach($test_cases as $test_case){
  if($test_case->success){
    $test_case->printEvaluation();
  }
}

// Remove temporary files if --noclean was not specified
if(!array_key_exists("noclean", $options)){
  foreach($test_cases as $test_case){
    $test_case->clean();
  }
}

print("</body>\n");
print("</html>\n");

?>
