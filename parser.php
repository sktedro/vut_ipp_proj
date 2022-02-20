<?php // Author: Patrik Skaloš

/*
 * PHP naming conventions:
 *
 * ClassName
 * functionName
 * methodName
 * variable_name
 * CONSTANTS_AND_ENUMS
 */


ini_set('display_errors', 'stderr');


/*
 * Constants
 */


define("USAGE",
"Brief:
  This script reads the IPPcode22 code from standard input, analyzes it 
  lexically and syntatically and if the code is valid, corresponding XML 
  document is generated and written to standard output.

Requirements:
  Requires php 8.1

Usage:
  php parse.php [--help]
");


define("ARG_TYPES", [
  "var"   => 0,
  "symb"  => 1,
  "label" => 2,
  "type"  => 3
]);


// Arrays defining what argument types the instructions need or support
define("INSTR_ARGS", [
  "MOVE"        => [ARG_TYPES["var"], ARG_TYPES["symb"]],
  "CREATEFRAME" => [],
  "PUSHFRAME"   => [],
  "POPFRAME"    => [],
  "DEFVAR"      => [ARG_TYPES["var"]],
  "CALL"        => [ARG_TYPES["label"]],
  "RETURN"      => [],
  "PUSH"        => [ARG_TYPES["symb"]],
  "POPS"        => [ARG_TYPES["var"]],
  "ADD"         => [ARG_TYPES["var"], ARG_TYPES["symb"], ARG_TYPES["symb"]],
  "SUB"         => [ARG_TYPES["var"], ARG_TYPES["symb"], ARG_TYPES["symb"]],
  "MUL"         => [ARG_TYPES["var"], ARG_TYPES["symb"], ARG_TYPES["symb"]],
  "IDIV"        => [ARG_TYPES["var"], ARG_TYPES["symb"], ARG_TYPES["symb"]],
  "LT"          => [ARG_TYPES["var"], ARG_TYPES["symb"], ARG_TYPES["symb"]],
  "GT"          => [ARG_TYPES["var"], ARG_TYPES["symb"], ARG_TYPES["symb"]],
  "EQ"          => [ARG_TYPES["var"], ARG_TYPES["symb"], ARG_TYPES["symb"]],
  "AND"         => [ARG_TYPES["var"], ARG_TYPES["symb"], ARG_TYPES["symb"]],
  "OR"          => [ARG_TYPES["var"], ARG_TYPES["symb"], ARG_TYPES["symb"]],
  "NOT"         => [ARG_TYPES["var"], ARG_TYPES["symb"], ARG_TYPES["symb"]],
  "INT2CHAR"    => [ARG_TYPES["var"], ARG_TYPES["symb"]],
  "STRI2INT"    => [ARG_TYPES["var"], ARG_TYPES["symb"], ARG_TYPES["symb"]],
  "READ"        => [ARG_TYPES["var"], ARG_TYPES["type"]],
  "WRITE"       => [ARG_TYPES["symb"]],
  "CONCAT"      => [ARG_TYPES["var"], ARG_TYPES["symb"], ARG_TYPES["symb"]],
  "STRLEN"      => [ARG_TYPES["var"], ARG_TYPES["symb"]],
  "GETCHAR"     => [ARG_TYPES["var"], ARG_TYPES["symb"], ARG_TYPES["symb"]],
  "SETCHAR"     => [ARG_TYPES["var"], ARG_TYPES["symb"], ARG_TYPES["symb"]],
  "TYPE"        => [ARG_TYPES["var"], ARG_TYPES["symb"]],
  "LABEL"       => [ARG_TYPES["label"]],
  "JUMP"        => [ARG_TYPES["label"]],
  "JUMPIFEQ"    => [ARG_TYPES["label"], ARG_TYPES["symb"], ARG_TYPES["symb"]],
  "JUMPIFNEQ"   => [ARG_TYPES["label"], ARG_TYPES["symb"], ARG_TYPES["symb"]],
  "EXIT"        => [ARG_TYPES["symb"]],
  "DPRINT"      => [ARG_TYPES["symb"]],
  "BREAK"       => []
]);


// Regular expressions to test for validity of instruction arguments
define("REGEXES", [
  "var"    => "/^(TF|LF|GF)@[a-zA-Z_\\-$&%*!?][a-zA-Z1-9_\\-$&%*!?]*$/",
  "int"    => "/^int@[\\+|\\-]?[0-9]$/",
  "bool"   => "/^bool@(true|false)$/",
  "string" => "/^string@([a-zA-Z!\"\$-\\[\\]-~]|(\\\\\\d\\d\\d))+$/",
  "nil"    => "/^nil@nil$/",
  "label"  => "/^[a-zA-Z_\\-$&%*!?][a-zA-Z0-9_\\-$&%*!?]*$/",
  "type"   => "/^(int|bool|string|nil)$/"
]);


/*
 * Classes
 */


class XML{
  private $dom;
  private $xml_root;
  private $xml_output;


  // Initialize the XML DOM
  function __construct(){
    $this->dom = new DOMDocument('1.0', 'UTF-8');
    $this->xml_root = $this->dom->createElement("program");
    $this->addAttrib($this->xml_root, "language", "IPPcode22");
  }


  // Add a new attribute to the parent
  function addAttrib($parent, $name, $val){
    $attrib = $this->dom->createAttribute($name);
    $attrib->value = $val;
    $parent->appendChild($attrib);
  }


  // Add a new instruction to the XML DOM
  function addInstruction($instruction){
    // Create a new element
    $instruction_xml = $this->dom->createElement("instruction");

    // Add order and instruction name (opcode) as attributes
    $this->addAttrib($instruction_xml, "order", $instruction->order);
    $this->addAttrib($instruction_xml, "opcode", $instruction->opcode);

    // Add all arguments of the instruction as children
    for($i = 0; $i < count($instruction->args); $i++){
      $arg = $instruction->args[$i];

      // Create an argument element with name arg1/2/3 and also write the value
      $arg_element = $this->dom->createElement("arg" . strval($i + 1), $arg[1]);

      // Set the type attribute
      $this->addAttrib($arg_element, "type", $arg[0]);

      // Append the argument element to the parent (instruction)
      $instruction_xml->appendChild($arg_element);
    }

    // Append the instruction to the XML DOM
    $this->xml_root->appendChild($instruction_xml);
  }


  // Finalize the DOM, save it as XML and return it
  function generateOutput(){
    $this->dom->appendChild($this->xml_root);
    $this->dom->formatOutput = true;
    $this->xml_output = $this->dom->saveXML();
    return $this->xml_output;
  }
}


class Instruction{
  public $order;
  public $opcode;
  public $args;
  public $xml;


  // Split the line and convert first line element (instruction code) to
  // uppercase
  function __construct($order, $line){

    // Save the instruction order
    $this->order = $order;

    // Split the line at spaces, convert the opcode to uppercase, save it and 
    // save the arguments separately
    $this->args = explode(' ', $line);
    $this->opcode = strtoupper(array_shift($this->args));
  }


  // Check instruction arguments
  function parseInstruction(){

    // Check if the opcode is valid
    if(array_key_exists($this->opcode, INSTR_ARGS)){
      $required_args = INSTR_ARGS[$this->opcode];
    }else{
      trigger_error("Unknown instruction: '" . $this->opcode . "'", E_USER_ERROR);
      exit(22);
    }

    // Check if the amount of arguments of the instruction is right
    if(count($required_args) != count($this->args)){
      trigger_error("Invalid amount of arguments (" . count($this->args) . " instead of " . count($required_args) . ") for instruction: '" . $this->opcode . "'", E_USER_ERROR);
      exit(23);
    }

    // Parse the arguments if they match a regex
    for($i = 0; $i < count($required_args); $i++){
      $arg = $this->args[$i];

      // Var must be a variable identifier (eg. LF@_123abc)
      if($required_args[$i] == ARG_TYPES["var"] 
          && preg_match(REGEXES["var"], $arg)){

        $this->args[$i] = ["var", $arg];

      // Symbol can be a variable
      }else if($required_args[$i] == ARG_TYPES["symb"] 
          && preg_match(REGEXES["var"], $arg)){

        $this->args[$i] = ["var", $arg];

      // Symbol can be a literal
      }else if($required_args[$i] == ARG_TYPES["symb"]
          && (preg_match(REGEXES["int"], $arg)
            || preg_match(REGEXES["bool"], $arg)
            || preg_match(REGEXES["string"], $arg)
            || preg_match(REGEXES["nil"], $arg))){

        $this->args[$i] = explode('@', $arg);

        // Convert [&<>"'] to XML friendly strings if the arg is a string
        if($this->args[$i][0] == "string"){
          $this->args[$i][1] = htmlspecialchars($this->args[$i][1], ENT_XML1 | ENT_QUOTES, "UTF-8");
        }

      // Label must be a label identifier (similar to a variable)
      }else if($required_args[$i] == ARG_TYPES["label"] 
          && preg_match(REGEXES["label"], $arg)){

        $this->args[$i] = ["label", $arg];

      // Type must be a variable type
      }else if($required_args[$i] == ARG_TYPES["type"] 
          && preg_match(REGEXES["type"], $arg)){

        $this->args[$i] = ["type", $arg];

      // No regex match!
      }else{
        trigger_error("Bad argument: '" . $this->args[$i] . "' for instruction: '" . $this->opcode . "'", E_USER_ERROR);
        exit(23);
      }
    }
  }
}


/*
 * Functions
 */


// Remove comments and unnecessary white spaces from a line
function trimLine($line){

  // Search for '#' and if found, only get characters before it
  $pos = strpos($line, "#", 0);
  if($pos){
    $line = substr($line, 0, $pos);
  }

  // Replace '\t' by ' '
  $line = str_replace("\t", " ", $line);

  // Replace "  " by " " so there won't be two subsequent spaces
  while(strpos($line, "  ", 0)){
    $line = str_replace("  ", " ", $line);
  }

  // Remove the last character of a line if it is a newline or a space
  $line = rtrim($line, "\n\r ");

  // Remove the fist character of a line if it is a space
  $line = ltrim($line, " ");

  return $line;
}


// Check user-provided arguments
function checkArgs($argc, $argv){
  if($argc > 1){
    if($argc == 2 && $argv[1] == "--help"){
      echo(USAGE);
      exit(0);
    }else{
      trigger_error("Could not parse arguments provided", E_USER_ERROR);
      exit(10);
    }
  }
}


// Check for the .IPPcode22 header (case insensitive)
function checkInputHeader(){
  while($line = fgets(STDIN)){

    // Remove redundant whitespaces from the line
    $line = trimLine($line);

    // Header found? Return
    if(!strcmp(strtoupper($line), ".IPPCODE22")){
      return;
    }

    // Header not found but line is not empty or contains non-space character?
    if(strlen($line) > 0 || $line[0] != ' '){
      break;
    }
  }

  // Header not found!
  trigger_error("Wrong or no header was found in the provided code", E_USER_ERROR);
  exit(21);
}


/*
 *
 * Main program flow
 *
 */


// Check user-provided arguments
checkArgs($argc, $argv);

// Check for the .IPPcode22 header (case insensitive)
checkInputHeader();

// Create a empty XML DOM to write the code into
$xml = new XML();

// Keep track of instruction order
$order = 1;

// Read line by line from the standard input
while($line = fgets(STDIN)){

  // Trim redundant white characters from the received line
  $line = trimLine($line);

  // Create and initialize an instruction given the order and the read line
  $instruction = new Instruction($order, $line);

  // Parse the line to get instruction arguments
  $instruction->parseInstruction();

  // Add the instruction to the XML DOM
  $xml->addInstruction($instruction);

  $order++;
}

// Generate the XML output and print it to the standard output
echo($xml->generateOutput());

?>
