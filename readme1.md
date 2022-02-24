# Implementation documentation to task 1 for IPP 2021/2022



#### Name and surname: Patrik Skaloš

#### Login: xskalo01


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
