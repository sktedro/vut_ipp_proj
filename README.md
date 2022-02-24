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



# Interpret


### Usage


# Testing script


### Usage
