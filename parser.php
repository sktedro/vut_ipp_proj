<?php

// Author: Patrik Skaloš

/*
 * ClassName
 * functionName
 * methodName
 * variable_name
 */

// Návrhový vzor?

ini_set('display_errors', 'stderr');

enum ARG_TYPES{
  case ARG_VAR;
  case ARG_SYMB;
  case ARG_LABEL;
  case ARG_TYPE;
}

$INSTR_ARGS = [
  "MOVE"        => [ARG_TYPES::ARG_VAR, ARG_TYPES::ARG_SYMB],
  "CREATEFRAME" => [],
  "PUSHFRAME"   => [],
  "POPFRAME"    => [],
  "DEFVAR"      => [ARG_TYPES::ARG_VAR],
  "CALL"        => [ARG_TYPES::ARG_LABEL],
  "RETURN"      => [],
  "PUSH"        => [ARG_TYPES::ARG_SYMB],
  "POPS"        => [ARG_TYPES::ARG_VAR],
  "ADD"         => [ARG_TYPES::ARG_VAR, ARG_TYPES::ARG_SYMB, ARG_TYPES::ARG_SYMB],
  "SUB"         => [ARG_TYPES::ARG_VAR, ARG_TYPES::ARG_SYMB, ARG_TYPES::ARG_SYMB],
  "MUL"         => [ARG_TYPES::ARG_VAR, ARG_TYPES::ARG_SYMB, ARG_TYPES::ARG_SYMB],
  "IDIV"        => [ARG_TYPES::ARG_VAR, ARG_TYPES::ARG_SYMB, ARG_TYPES::ARG_SYMB],
  "LT"          => [ARG_TYPES::ARG_VAR, ARG_TYPES::ARG_SYMB, ARG_TYPES::ARG_SYMB],
  "GT"          => [ARG_TYPES::ARG_VAR, ARG_TYPES::ARG_SYMB, ARG_TYPES::ARG_SYMB],
  "EQ"          => [ARG_TYPES::ARG_VAR, ARG_TYPES::ARG_SYMB, ARG_TYPES::ARG_SYMB],
  "AND"         => [ARG_TYPES::ARG_VAR, ARG_TYPES::ARG_SYMB, ARG_TYPES::ARG_SYMB],
  "OR"          => [ARG_TYPES::ARG_VAR, ARG_TYPES::ARG_SYMB, ARG_TYPES::ARG_SYMB],
  "NOT"         => [ARG_TYPES::ARG_VAR, ARG_TYPES::ARG_SYMB, ARG_TYPES::ARG_SYMB],
  "INT2CHAR"    => [ARG_TYPES::ARG_VAR, ARG_TYPES::ARG_SYMB],
  "STRI2INT"    => [ARG_TYPES::ARG_VAR, ARG_TYPES::ARG_SYMB, ARG_TYPES::ARG_SYMB],
  "READ"        => [ARG_TYPES::ARG_VAR, ARG_TYPES::ARG_TYPE],
  "WRITE"       => [ARG_TYPES::ARG_SYMB],
  "CONCAT"      => [ARG_TYPES::ARG_VAR, ARG_TYPES::ARG_SYMB, ARG_TYPES::ARG_SYMB],
  "STRLEN"      => [ARG_TYPES::ARG_VAR, ARG_TYPES::ARG_SYMB],
  "GETCHAR"     => [ARG_TYPES::ARG_VAR, ARG_TYPES::ARG_SYMB, ARG_TYPES::ARG_SYMB],
  "SETCHAR"     => [ARG_TYPES::ARG_VAR, ARG_TYPES::ARG_SYMB, ARG_TYPES::ARG_SYMB],
  "TYPE"        => [ARG_TYPES::ARG_VAR, ARG_TYPES::ARG_SYMB],
  "LABEL"       => [ARG_TYPES::ARG_LABEL],
  "JUMP"        => [ARG_TYPES::ARG_LABEL],
  "JUMPIFEQ"    => [ARG_TYPES::ARG_LABEL, ARG_TYPES::ARG_SYMB, ARG_TYPES::ARG_SYMB],
  "JUMPIFNEQ"   => [ARG_TYPES::ARG_LABEL, ARG_TYPES::ARG_SYMB, ARG_TYPES::ARG_SYMB],
  "EXIT"        => [ARG_TYPES::ARG_SYMB],
  "DPRINT"      => [ARG_TYPES::ARG_SYMB],
  "BREAK"       => []
];

$REGEXES = [
  "var"    => "/^(TF|LF|GF)@[a-zA-Z_\\-$&%*!?][a-zA-Z1-9_\\-$&%*!?]*$/",
  "int"    => "/^int@[\\+|\\-]?[0-9]$/",
  "bool"   => "/^bool@(true|false)$/",
  "string" => "/^string@([a-zA-Z!\"\$-\\[\\]-~]|(\\\\\\d\\d\\d))+$/",
  "nil"    => "/^nil@nil$/",
  "label"  => "/^[a-zA-Z_\\-$&%*!?][a-zA-Z0-9_\\-$&%*!?]*$/",
  "type"   => "/^(int|bool|string|nil)$/"
];

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
  function parseArgs($INSTR_ARGS, $REGEXES){
    if(array_key_exists($this->opcode, $INSTR_ARGS)){
      $required_args = $INSTR_ARGS[$this->opcode];
    }else{
      trigger_error("Unknown instruction: '" . $this->opcode . "'", E_USER_ERROR);
      exit(22);
    }
    if(count($required_args) != count($this->args)){
      trigger_error("Invalid amount of arguments (" . count($this->args) . " instead of " . count($required_args) . ") for instruction: '" . $this->opcode . "'", E_USER_ERROR);
      exit(23);
    }

    // Parse the arguments if they match a regex
    for($i = 0; $i < count($required_args); $i++){
      $arg = $this->args[$i];

      // Must be a variable identifier (eg. LF@_123abc)
      if($required_args[$i] == ARG_TYPES::ARG_VAR && preg_match($REGEXES["var"], $arg)){
        $this->args[$i] = ["var", $arg];

      // Symbol can be a variable
      }else if($required_args[$i] == ARG_TYPES::ARG_SYMB && preg_match($REGEXES["var"], $arg)){
        $this->args[$i] = ["var", $arg];

      // Symbol can be a literal
      }else if($required_args[$i] == ARG_TYPES::ARG_SYMB
          && (preg_match($REGEXES["int"], $arg)
            || preg_match($REGEXES["bool"], $arg)
            || preg_match($REGEXES["string"], $arg)
            || preg_match($REGEXES["nil"], $arg))){
        $this->args[$i] = explode('@', $arg);
        // Convert & < > " ' to XML friendly strings if the arg is a string
        if($this->args[$i][0] == "string"){
          $this->args[$i][1] = htmlspecialchars($this->args[$i][1], ENT_XML1 | ENT_QUOTES, "UTF-8");
        }

      // Must be a label identifier (similar to a variable)
      }else if($required_args[$i] == ARG_TYPES::ARG_LABEL && preg_match($REGEXES["label"], $arg)){
        $this->args[$i] = ["label", $arg];

      // Must be a variable type
      }else if($required_args[$i] == ARG_TYPES::ARG_TYPE && preg_match($REGEXES["type"], $arg)){
        $this->args[$i] = ["type", $arg];

      // No regex match!
      }else{
        trigger_error("Bad argument: '" . $this->args[$i] . "' for instruction: '" . $this->opcode . "'", E_USER_ERROR);
        exit(23);
      }
    }
  }

  function generateXML($dom){
    $this->xml = $dom->createElement("instruction");

    $order = $dom->createAttribute("order");
    $order->value = $this->order;
    $this->xml->appendChild($order);

    $opcode = $dom->createAttribute("opcode");
    $opcode->value = $this->opcode;
    $this->xml->appendChild($opcode);

    for($i = 0; $i < count($this->args); $i++){
      $arg = $this->args[$i];
      $arg_element = $dom->createElement("arg" . strval($i + 1), $arg[1]);
      $arg_type = $dom->createAttribute("type");
      $arg_type->value = $arg[0];
      $arg_element->appendChild($arg_type);
      $this->xml->appendChild($arg_element);
    }
  }
}

// Remove comments and unnecessary white spaces from a line
function trimLine($line){

  // Search for '#' and if found, only get characters before it
  $pos = strpos($line, "#", 0);
  if($pos){
    $line = substr($line, 0, $pos);
  }

  // Replace '\t' by ' '
  $line = str_replace("\t", " ", $line);

  // Replace "  " by " "
  while(strpos($line, "  ", 0)){
    $line = str_replace("  ", " ", $line);
  }

  // Remove the last character of a line if it is a newline or a space
  $line = rtrim($line, "\n\r ");

  // Remove the fist character of a line if it is a space
  $line = ltrim($line, " ");

  return $line;
}



// Check for --help param
if($argc > 1){
  if($argc == 2 && $argv[1] == "--help"){
    echo("Usage:");
    // TODO
  }else{
    // TODO exit
    trigger_error("Could not parse arguments provided", E_USER_ERROR);
  }
}

$order = 1;


$header_found = False;
while($line = fgets(STDIN)){
  $line = trimLine($line);
  if(strlen($line) != 0){
    if(!strcmp(strtoupper($line), ".IPPCODE22")){
      $header_found = True;
      break;
    }
  }
}
if(!$header_found){
  trigger_error("Wrong or no header was found in the provided code", E_USER_ERROR);
  exit(21);
}

$dom = new DOMDocument('1.0', 'UTF-8');
$xml_root = $dom->createElement("program");
$xml_root_attrib = $dom->createAttribute('language');
$xml_root_attrib->value = "IPPcode22";
$xml_root->appendChild($xml_root_attrib);

// Read line by line from stdin
while($line = fgets(STDIN)){
  $line = trimLine($line);
  $instruction = new Instruction($order, $line);
  $instruction->parseArgs($INSTR_ARGS, $REGEXES);
  $instruction->generateXML($dom);
  $xml_root->appendChild($instruction->xml);

  $order++;
}

// </program>
$dom->appendChild($xml_root);

$dom->formatOutput = true;
$xml_output = $dom->saveXML();
echo($xml_output);

?>
