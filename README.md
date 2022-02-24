# Brief: IPP project

This repository contains a parser written in PHP, an interpret written in Python
and a testing script for both of them also written in PHP. The parser takes a
source code written in IPPcode22 programming language and outputs its
representation in a XML format. The interpret takes the code in XML format and
simply runs is. The testing script is a bit more complicated and will be
explained later, but put simply, it takes inputs and reference outputs of all
test cases in a provided folder, runs the test target for every one these inputs
and compares the outputs with the reference outputs. Finally, it evaluates the
tests by printing a report in HTML format which is to be forwarded to a .html
file and read in a browser by the user.



# Parser


### Requirements

php 8.1


### Documentation

#### Reading the source code

The source code to be parsed is read from the standard input line by line.
Since the code must not contain any instructions preceding a header 
(`.IPPcode22`), a function `checkInputHeader` first reads lines in a loop until
the header is found. Only if the header is present, a simple XML object is 
created as a new `DOMDocument` object with the required header and a root 
element. After that, the source code is read line by line in a loop, while every
line is trimmed of redundant characters (spaces, newline character, comments, 
...) and parsed in a following way: 

#### Checking and parsing source code lines

If the line is not empty, it is assumed it contains an instruction and a new 
`Instruction` object is created. This object consists of `order`, `opcode`
(instruction name) and `args` of the instruction, which the line is parsed into.
The parsing process is pretty simple thanks to an array containing required
argument types for each instruction. First, we need to check if the `opcode` is
in that array and then, based on types of arguments required, we can try to
match the arguments to a regular expression. If that fails, the argument is
evaluated as invalid. Otherwise, the argument is appended to the `args` array of
the `Instruction` object. We also need to convert strings and names to only
contain XML friendly characters, eg. `&` is converted to `&amp`.

#### Converting the instruction to XML format

After the instruction is parsed, we call a method `addInstruction` to convert
it to the XML format. Example for the `LABEL` instruction:
```
<instruction order="1" opcode="LABEL">
  <arg1 type="label">labelName</arg1>
</instruction>
```

After the instruction is represented as a XML element, it is appended to the
XML root element which then acts as a list of instructions.

#### Finishing

Only when all lines (instructions) have been read, `generateOutput` method of
our `XML` class is called to convert the created XML structure to a string which
is then printed to the standard output - this makes the parsing finish
successfully.

#### Note

Of course, every step of the way the code is inspected for lexical and
syntactic errors and in case of finding any, the parsing stops and returns an
appropriate return value while reporting the error to the standard error output.


### Usage

#### Reading the source code from the standard input

```
php8.1 parse.php [--help]
```

#### Reading the source code from a file

```
php8.1 parse.php [--help] < relative/or/absolute/path/to/file
```



# Interpret


### Requirements

Python 3.8


### Documentation

#### Initialization

First, arguments are parsed and the source code is read to verify integrity and
get the root element of the file.

#### Reading the instructions

The script iterates through all elements with the tag equal to `instruction`,
reads the attributes and creates `Instruction` objects. For each instruction
element it also iterates through all the sub-elements (arguments), parses
them by creating `Argument` objects and appends them to an array stored in the 
`Instruction` object. Every `Instruction` object also stores its order and
opcode and provides methods to add an argument and run the instruction.

#### Reading the arguments

Every `Argument` object stores argument's order, type (which can be an argument 
type or a data type if the argument is a literal) and a value which is just a
raw text extracted from the XML element. Order and value of each argument is, of
course, checked for validity (at times using regular expression). `Argument`
objects provide methods to get their value or data type (of a variable if the 
argument is a variable).

#### Program

Everything about the interpretation is stored in a global variable which is an
instance of class `Program`. This class stores the input file, instructions
sorted by their orders, a symbol table, a list of labels, a data stack and a
return (function call) stack. The `Program` class provides methods to jump after
an instruction, jump to a label and run all instructions in a loop. After the
`Program` object has been constructed, the only thing left to do is to run all
instructions one by one, which is done by the mentioned method of this class
called from the main function.

#### Symbol table

A symbol table needed to be implemented for the interpretation and is a class
`SymTab`
consisting of a global frame, temporary frame and a list of local frames. Every
frame is just a dictionary where variables are stored by name as objects, while
having these four attributes: `declared` (boolean), `defined` (boolean),
`type` (data type, string), `val` (string). The symtable provides methods to
declare and define a variable, to check if a variable is declared/defined at the
moment and to get the variable as an object containing the mentioned attributes.

#### Instruction execution

A dictionary of dictionaries was implemented to provide a simple way to get
information about instructions. In this dictionary, there is a dictionary for
every instruction by an instruction opcode (instruction name), which contains a
pointer to a function which executes the instruction, required argument types
(`var`, `symb`, ...), required data types of arguments (`int`, `bool`, `string`,
`nil`, `any` for no requirement and `eq` which simply indicates that all
arguments with requirement `eq` need to be equal) and a requirement of the
argument state in the symbol table (`none`, `declared`, `defined`) for each
argument. Example for instruction with opcode `JUMP`:
```
"JUMP":        {                  
    "function":     Exec.e_jump,  
    "types":        ["label"   ], 
    "data_types":   ["any"     ], 
    "requirements": ["defined" ]},
```
This tells the script to call function `e_jump` of class `Exec` to execute the
instruction, that it takes one argument of type `label` and any data type while
the label also needs to be already defined when executing.

To run the instruction, it's method `run` is called. This method is a huge
function checking if all requirements are met (if the arguments are
declared/defined if they need to be, if they are the right types and data
types) and if everything checks out, a function from the class `Exec` is called
to interpret the instruction. The `Exec` class doesn't need to be a separate
class since it only contains methods, but I thought the code might be clearer
if the methods are called as the class members.

##### A few examples of instruction execution functions

Most of these functions are very simple thanks to the fact that most of the
things that need to be checked before executing were checked already (eg. we
know that the data types are right so we don't need to check that in every of
these functions).

`Exec.e_call`: appends the instruction that is being executed in the moment to
the `Program.return_stack` and calls `Exec.e_jump` function with the same 
arguments as it received.

`Exec.e_pops`: calls python's `pop` function on `Program.data_stack`. If it
fails, exit with a value `56`, otherwise, call `Program.symtab.define` on the
first argument while providing the type and value of the popped item.

`Exec.e_write`: if the data type of the first argument is not `nil`, print the
argument's value to the standard output without the new line character at the
end. Otherwise, do nothing.

#### Note

Of course, every step of the way, various errors are checked for. I only
mentioned a few of those in this documentation. If an error occurs, the script
returns with an appropriate value after reporting the error to the standard
error output (in most cases also indicating where and why was the error 
invoked).


### Usage

```
interpret.py [-h] [--source SOURCE] [--input INPUT]

Options:
  -h, --help       show this help message and exit
  --source SOURCE  Source code of a IPPcode22 program in XML format. If not 
      provided, code will be read from standard input
  --input INPUT    Input for the source code implementation. If not provided, 
      input will be forwarded from standard input
```



# Testing script


### Requirements

php 8.1


### Documentation

#### Initialization

First, all arguments are processed one by one and checked for validity. After
that, the beginning of the (HTML) report that will be the output of this script
is generated.

#### Fetching all test files

The script searches the provided directory for files with `.src` extension
which will define a single test case. If `--recursive` option is selected, it
recursively search all subfolders as well. The output of this action is an
array of `TestCase` objects. 

#### Initialization of the test cases

Each one of `TestCase` objects contains the directory in which the source files
are located, name of the test case, paths to all files of the test case (source 
file, input, output, return code, temporary stdout file, temporary stderr file 
and temporary diff file), code retuned by the target after test execution and a
boolean variable indicating if the test was successful. When constructing a
`TestCase` object, paths where to find all necessary files are generated and if
some of them don't exist, they are generated using a command `touch` (except for
the `.rc` file since a character (`0`) needs to be written to it).

#### Executing the tests

Tests are executed one by one in a way that depends on the target provided. If
only testing the parser or the interpret, the script is ran with the input
files. If both the parser and interpret are to be tested at once, the output
of the parser is simply forwarded to the interpret.
The standard output and standard error output are saved to temporary files and
the code returned by the execution is stored in a variable.

#### Evaluating the tests

A test is considered successful if the returned value is not `0` but matches
the reference return value, or if the returned value is `0` and the output
matches the reference output. If the parser is the test target, difference
between outputs is checked using `JExamXML`, otherwise, `diff` command is used.

#### Generating the report

First, an overview is generated stating the test target, a number of successful
tests and a number of total tests. After that, evaluations of failed tests are
printed into dark red blocks containing information about the failed test: test
path, code input and standard error output. If the test didn't pass
because of a wrong value returned, expected and received return values are
printed as well. Otherwise, if the test didn't pass because the outputs didn't
match, expected and received outputs are printed instead. After evaluations of
failed tests, test path and code input is also printed for every successful test
in dark green blocks.

#### Finishing

The only thing to do after the report has been generated is to remove all
temporary files created by the testing script. This is, however, only done if
the user did not specify the `--noclean` argument.


### Usage

```
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
```
