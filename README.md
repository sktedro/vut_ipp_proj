# Brief: IPP project

This repository contains a parser written in PHP, interpret written in Python
and testing script for both of them also written in PHP. The parser takes a
source code written in IPPcode22 programming language and outputs its
representation in a XML format. The interpret takes the code in XML format and
simply runs is. The testing script is a bit more complicated and will be
explained later, but put simply, it takes inputs and reference outputs of a
test case from a provided folder, runs the test target and compares the outputs
with the reference outputs. Finally, evaluates the tests by printing the
evaluation in HTML format which is to be forwarded to a .html file and read in
a browser.



# Parser


### Requirements

php 8.1


### Documentation

#### Reading the source code

The source code to be parsed is read from the standard input line by line.
Since the code must not contain any instructions preceding a header 
(`IPPcode22`), a function checkInputHeader() first reads lines in a loop until
the header is found. Only if the header is present, a simple XML object is 
created as a new DOMDocument object with an appropriate header and root element.
After that, the source code is read line by line in a loop, while every line is
trimmed of redundant characters (spaces, newline character, comments, ...). 

#### Checking and parsing source code lines

If the line is not empty, it is assumed it contains an instruction and a new 
Instruction object is created. It consists of `order`, `opcode` (name) and 
`args` of the instruction, which the line is parsed into. The parsing process
is pretty simple thanks to an array containing required argument types for each
instruction. First, we need to check if the `opcode` is in that array and then,
based on types of arguments required, we can try to match the arguments to a
regular expression. If that fails, the argument is invalid. Otherwise, the
argument is appended to the `args` array of the Instruction object. We also
need to convert strings and names to only contain XML friendly characters, eg.
`&` is converted to `&amp`.

#### Converting the instruction to XML format

After the instruction is parsed, we call a function addInstruction() to convert
it to the XML format. Example for a LABEL instruction:
```
<instruction order="1" opcode="LABEL">
  <arg1 type="label">labelName</arg1>
</instruction>
```

After the instruction is represented as a XML element, it is appended to the
XML root element which then acts as a list of instructions.

#### Finishing

Only when all lines (instructions) have been read, generateOutput() function of
our XML class is called to convert the XML created structure to a string which
is then printed to the standard input - this makes the parsing finish
successfully.

#### Note

Of course, every step of the way the code is inspected for lexical and
syntactic errors and in case of finding any, the parsing stops and returns an
appropriate return value.


### Usage

#### Reading the source code from the standard input

php8.1 parse.php [--help]

#### Reading the source code from a file

php8.1 parse.php [--help] < relative/or/absolute/path/to/file



# Interpret TODO


### Usage



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
array of TestCase objects. 

#### Initialization of the test cases

Each of TestCase objects contains the directory in which the source files are 
located, name of the test case, paths to all files of the test case (source 
file, input, output, return code, temporary stdout file, temporary stderr file 
and temporary diff file), code retuned by the target after test execution and a
boolean variable indicating if the test was successful. The first step of a
test case initialization is generating paths where to find all necessary files 
and if some of them don't exist, they are generated.

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
between outputs is checked using JExamXML, otherwise, `diff` command is used.

#### Generating the report

First, an overview is generated stating the test target, a number of successful
tests and a number of total tests. After that, evaluations of failed tests are
printed into dark red blocks containing information about the failed test: test
path, code input and standard error output are printed. If the test didn't pass
because of a wrong value returned, expected and received return values are
printed. Otherwise, if the test didn't pass because the outputs didn't match,
expected and received outputs are printed. After evaluations of failed tests,
test path and code input is also printed for every successful test in dark
green blocks.

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
