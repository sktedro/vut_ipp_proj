# interpret.py
# Author: Patrik Skaloš
# Warning: This script is not to be imported as a module

import re
import argparse
import xml.etree.ElementTree as ET
import sys
import operator

# TODO checking if var defined (declared)

#
#
# Miscellaneous functions
#
#


# Print an error and exit if an exit code was provided
# TODO also print opcode and args?
def err(code, *text):
    for i in range(len(text)):
        sys.stderr.write(text[i])
    if code != None:
        sys.stderr.write(". Exiting\n")
        exit(code)
    else:
        sys.stderr.write("\n")

# Print an error and the current location and exit if an exit code was provided
# TODO also print opcode and args?
def code_err(code, *text):
    sys.stderr.write("Error at instruction #" + str(program.prev_order) + ": ")
    for i in range(len(text)):
        sys.stderr.write(text[i])
    if code != None:
        sys.stderr.write(". Exiting\n")
        exit(code)
    else:
        sys.stderr.write("\n")

def check_type(arg, dt):
    return arg.symb_type() == dt

# Check if the data types of arguments match to strings provided in *types
def check_types(args, *types):
    if isinstance(args, Argument):
        args = [args]
    for i in range(len(args)):
        if args[i].symb_type() != types[i]:
            code_err(53, "Wrong data type: requires " + types[i] + " but received " + args[i].symb_type())


#
#
# Classes
#
#


# A single object containing all information about the interpretation
class Program:
    def __init__(self, input_file, instructions):
        self.input_file = input_file
        self.instructions = instructions
        self.labels = []
        self.prev_order = 0
        self.data_stack = []
        self.return_stack = []
        self.symtab = SymTab()

        # Check for duplicit orders of instructions in the XML file
        orders_of_instrs = []
        for i in instructions:
            if i.order in orders_of_instrs:
                err(32, "Duplicit orders of instructions:", str(i.order))
            orders_of_instrs.append(i.order)

        # TODO sort instructions?

        # Get all labels
        for instr in self.instructions:
            if instr.opcode == "LABEL":

                # Check the label arg type
                check_types(instr.args[0], "label")

                # Create the new label
                label = {
                    "name": instr.args[0].symb_val(),
                    "order": instr.order
                    }

                # Make sure a label with that name doesn't already exist
                for existing_label in self.labels:
                    if label["name"] == existing_label["name"]:
                        err(52, "Label name " + label["name"] + " used twice")
                self.labels.append(label)


    # Returns a new line from the input file (can be stdin)
    def get_line_from_input(self):
        line = self.input_file.readline()
        if line[-1] == '\n':
            line = line[: -1]
        return line


    # Run the next instruction bsed on the order of the previous instruction
    def run_next(self):

        # Find the instruction with order higher than order of the previous
        # instruction but still lowest possible from available instructions
        next_instr = None
        for instr in self.instructions:
            if instr.order > self.prev_order:
                if next_instr == None or instr.order < next_instr.order:
                    next_instr = instr

        # If none is found, there are no more instructions to run
        if next_instr == None:
            return False

        # Otherwise, update the previous instruction order and run the next one
        self.prev_order = next_instr.order
        next_instr.run()


    # Jump to an instruction following the one with order equal to one provided
    def jump_after_order(self, order):
        self.prev_order = order


# A class containing functions that execute instructions
class Exec:

    # Does a binary mathematical operation specified by operator
    # args[0] = args[1] <operator> args[2]
    def math_op(args, operator):
        check_types(args[1: ], "int", "int")
        operand1 = int(args[1].symb_val())
        operand2 = int(args[2].symb_val())
        program.symtab.set(
                args[0], 
                "int", 
                str(operator(operand1, operand2))
                )

    # Does a binary boolean operation specified by operator
    # args[0] = args[1] <operator> args[2]
    def bool_binary_op(args, operator):
        check_types(args[1: ], "bool", "bool")
        operand1 = args[1].symb_val() == "true"
        operand2 = args[2].symb_val() == "true"
        program.symtab.set(
                args[0], 
                "bool", 
                operator(operand1, operand2)
                )

    # MOVE
    def e_move(args):
        program.symtab.set(
                args[0], 
                args[1].symb_type(), 
                args[1].symb_val()
                )

    # CREATEFRAME 
    def e_createframe(args):
        program.symtab.tf = {}

    # PUSHFRAME
    def e_pushframe(args):
        if program.symtab.tf == None:
            code_err(55, "Cannot push a temporary frame since none exists")
        program.symtab.lfs.append(program.symtab.tf)
        program.symtab.tf = None

    # POPFRAME
    def e_popframe(args):
        if len(program.symtab.lfs) == 0:
            code_err(55, "Cannot pop a temporary frame since none exists")
        # Move LF to TF by popping from LFs
        program.symtab.tf = program.symtab.lfs.pop()

    # DEFVAR
    def e_defvar(args):
        program.symtab.define(args[0])

    # CALL
    def e_call(args):
        program.return_stack.append(program.prev_order)
        Exec.e_jump(args)

    # RETURN
    def e_return(args):
        if len(program.return_stack) == 0:
            code_err(56, "Cannot return from a call, call stack is empty")
        program.jump_after_order(program.return_stack[-1])
        program.return_stack.pop()

    # PUSHS
    def e_pushs(args):
        arg_type = args[0].type
        arg_val = args[0].symb_val()
        program.data_stack.append({"type": arg_type, "val": arg_val})

    # POPS
    def e_pops(args):
        program.symtab.set(
                args[0], 
                program.data_stack[-1]["type"], 
                program.data_stack[-1]["val"]
                )
        program.data_stack.pop()

    # Binary mathematical operations:
    # ADD SUB MUL IDIV
    def e_add(args):
        Exec.math_op(args, operator.add)
    def e_sub(args):
        Exec.math_op(args, operator.sub)
    def e_mul(args):
        Exec.math_op(args, operator.mul)
    def e_idiv(args):
        if int(args[2].symb_val()) == 0:
            code_err(57, "Division by zero encountered")
        Exec.math_op(args, operator.floordiv)

    # Binary boolean operations:
    # LT GT EQ ADD OR
    def e_lt(args):
        Exec.bool_binary_op(args, operator.__lt__)
    def e_gt(args):
        Exec.bool_binary_op(args, operator.__gt__)
    def e_eq(args):
        Exec.bool_binary_op(args, operator.__eq__)
    def e_and(args):
        Exec.bool_binary_op(args, operator.__and__)
    def e_or(args):
        Exec.bool_binary_op(args, operator.__or__)

    # NOT
    def e_not(args):
        check_types(args[1], "bool")
        oprand = args[1].symb_val() == "true"
        program.symtab.set(
                args[0], 
                "bool", 
                not operand
                )

    # INT2CHAR
    def e_int2char(args):
        check_types(args[1], "int")
        try:
            result = chr(int(args[1].symb_val()))
        except:
            code_err(58, "Cannot convert integer to character: out of range")
        program.symtab.set(
                args[0], 
                "string", 
                result
                )

    # STR2INT
    def e_stri2int(args):
        check_types(args[1: ], "string", "int")
        try:
            result = str(ord(args[1].symb_val()[args[2].symb_val()]))
        except:
            code_err(58, "Cannot convert character to integer: out of range")
        program.symtab.set(
                args[0], 
                "int", 
                result
                )

    # READ
    def e_read(args):
        line = program.input_file.readline()
        if line[-1] == '\n':
            line = line[: -1]
        try:
            if args[1].val == "int":
                line = "int@" + str(int(line))
            elif args[1].val == "string":
                line = "int@" + line
            elif args[1].val == "bool":
                if line.upper() == "TRUE":
                    line = "bool@true"
                else:
                    line = "bool@false"
        except:
            line = "nil@nil"
        program.symtab.set(
                args[0], 
                line.split("@", 1)[0], 
                line.split("@", 1)[1]
                )

    # WRITE
    def e_write(args):
        if args[0].symb_type() != "nil":
            string = args[0].symb_val()
            if args[0].symb_type() == "string":
                # Convert all escaped sequences to characters
                while re.search("\\\(\\d{1,3})", string) != None:
                    match = re.search("\\\(\\d{1,3})", string)
                    sequence = string[match.span()[0]: match.span()[1]]
                    string = string.replace(sequence, chr(int(sequence[1: ])))
            print(string, end="")

    # CONCAT 
    def e_concat(args):
        check_types(args[1: ], "string", "string")
        program.symtab.set(
                args[0], 
                "string", 
                args[1].symb_val() + args[2].symb_val()
                )

    # STRLEN
    def e_strlen(args):
        check_types(args[1], "string")
        program.symtab.set(
                args[0], 
                "int", 
                len(args[1].symb_val())
                )

    # GETCHAR
    def e_getchar(args):
        check_types(args[1: ], "string", "int")
        string = args[1].symb_val()
        index = args[2].symb_val()
        if index < 0 or index >= len(string):
            code_err(58, "GETCHAR: index out of range")
        program.symtab.set(
                args[0], 
                "string", 
                string[int(index)]
                )

    # SETCHAR
    def e_setchar(args):
        check_types(args, "string", "int", "string")
        string = args[0].symb_val()
        index = int(args[1].symb_val())
        char = args[2].symb_val()
        if index < 0 or index >= len(string):
            code_err(58, "SETCHAR: index out of range")
        program.symtab.set(
                args[0], 
                "string", 
                string[: index] + char[0] + string[index + 1: ]
                )

    # TYPE
    def e_type(args):
        symb_type = args[1].symb_type()
        if symb_type == None:
            symb_type = ""
        program.symtab.set(
                args[0], 
                "string", 
                symb_type
                )

    # LABEL
    def e_label(args):
        pass # Pass, since the labels are already in the program.labels array

    # JUMP
    def e_jump(args):
        check_types(args[0], "label")
        label_name = args[0].symb_val()
        for label in program.labels:
            if label["name"] == label_name:
                program.jump_after_order(label["order"])
                return
        code_err(52, "Cannot jump to a non-existant label")

    # TODO refactored to this point

    # JUMPIFEQ
    def e_jumpifeq(args):
        if ((check_type(args[1], "nil") and args[2].symb_val == "nil") or 
                (args[1].symb_val == "nil" and check_type(args[2], "nil"))):
            Exec.e_jump([args[0]])
        elif args[1].symb_type() == args[2].symb_type():
            if args[1].symb_val() == args[2].symb_val():
                Exec.e_jump([args[0]])
        else:
            code_err(53, "JUMPIFEQ: data types not compatible")

    # JUMPIFNEQ
    def e_jumpifneq(args):
        if ((check_type(args[1], "nil") and args[2].symb_val != "nil") or 
                (args[1].symb_val != "nil" and check_type(args[2], "nil"))):
            e_jump([args[0]])
        elif args[1].symb_type() == args[2].symb_type():
            if args[1].symb_val() != args[2].symb_val():
                e_jump([args[0]])
        else:
            code_err(53, "JUMPIFNEQ: data types not compatible")

    # EXIT
    def e_exit(args):
        # TODO need to TRY to convert to int?
        check_types(args[0], "int")
        if not 0 <= int(args[0].symb_val()) <= 49:
            code_err(57, "Exit value is out of range of allowed values")
        exit(int(args[0].symb_val()))

    # DPRINT
    def e_dprint(args):
        code_err(None, args[0].symb_val())

    # BREAK
    def e_break(args):
        code_err(None, "Debugging info: ==================================")
        code_err(None, "Executing instruction #" + str(order))
        code_err(None, "Stack of instruction orders to return to:")
        code_err(None, "  " + str(program.return_stack))
        code_err(None, "Data stack contents: ")
        code_err(None, "  " + str(program.data_stack))
        code_err(None, "Symbol table contents:")
        code_err(None, "  Global frame: ")
        code_err(None, "    " + str(program.symtab.gf))
        code_err(None, "  Local frames: ")
        code_err(None, "    " + str(program.symtab.lfs))
        code_err(None, "  Temporary frame: ")
        code_err(None, "    " + str(program.symtab.tf))
        code_err(None, "==================================================")



# Class defining an instruction argument, consisting of:
#   order
#   type
#   data_type
#   val
class Argument:
    def __init__(self, arg_xml):
        if re.search("^arg[123]$", arg_xml.tag) == None:
            code_err(32, "Received an argument with invalid tag")
        else:
            try:
                self.order = int(arg_xml.tag[-1])
            except:
                code_err(32, "Wrong orders of arguments of a instruction")

        try:
            self.type = arg_xml.attrib["type"]
        except:
            code_err(31, "Received an argument without type specified")

        self.is_var = self.type == "var"

        self.val = arg_xml.text

        if not self.is_var:
            if self.type == "int":
                try:
                    int(self.val)
                except:
                    code_err(53, "Invalid integer literal")
            if self.type == "bool" and self.val != "true" and self.val != "false":
                code_err(53, "Invalid bool literal")
            if self.type == "nil" and self.val != "nil":
                code_err(53, "Nil data type can only contain value nil")


    def symb_val(self):
        if self.is_var:
            return program.symtab.get(self.val)["val"]
        else:
            return self.val

    def symb_type(self):
        if self.is_var:
            return program.symtab.get(self.val)["type"]
        else:
            return self.type

# Class defining an instruction, consisting of:
#   order
#   opcode
#   args
class Instruction:
    def __init__(self, opcode, order):
        try:
            if int(order) <= 0:
                code_err(32, "Order of an instruction is lower than 1")
        except:
            code_err(32, "Order of an instruction is not a number")
        self.order = int(order)
        self.opcode = opcode.upper()
        if not self.opcode in INSTRUCTIONS:
            code_err(32, "Invalid opcode:", self.opcode)
        self.args = []

    # Add an argument
    def add_arg(self, arg):
        self.args.append(Argument(arg))
        self.args.sort(key=lambda x: x.order)

    # Check orders of arguments
    def check_args(self):
        orders = []
        for arg in self.args:
            orders.append(arg.order)
        orders.sort()
        if orders not in [[], [1], [1, 2], [1, 2, 3]]:
            err(32, "Invalid arguments of an instruction #" + str(self.order))


    def run(self):
        INSTRUCTIONS[self.opcode]["function"](self.args)


class SymTab:
    def __init__(self):
        self.lfs = []
        self.gf = {}
        self.tf = None

    # TODO arr na defined vars ako lookup table? Alebo používať TRY pri
    # každom prístupe do symtab!!
    def def_in_frame(self, frame, name):
        if name in frame:
            code_err(52, "Redefinition of variable " + name)
        frame[name] = {}
        frame[name]["defined"] = True
        frame[name]["type"] = None
        frame[name]["val"] = None

    def get_frame(self, var):
        if isinstance(var, str):
            frame = var.split("@", 1)[0]
        else:
            frame = var.val.split("@", 1)[0]
        if frame == "GF":
            return self.gf
        elif frame == "TF":
            if self.tf == None:
                code_err(55, "Trying to use non-existant temporary frame")
            return self.tf
        else:
            if len(self.lfs) == 0:
                code_err(55, "Trying to use non-existant local frame")
            return self.lfs[-1]

    def get_name(self, var):
        if isinstance(var, str):
            return var.split("@", 1)[-1]
        else:
            return var.val.split("@", 1)[-1]

    def define(self, var):
        name = self.get_name(var)
        frame = self.get_frame(var)
        self.def_in_frame(frame, name)

    def set(self, var, literal_type, literal):
        name = self.get_name(var)
        frame = self.get_frame(var)
        frame[name]["val"] = literal
        frame[name]["type"] = literal_type

    def get(self, var):
        frame = self.get_frame(var)
        name = self.get_name(var)
        return frame[name]


# TODO done refactoring to this point

#
#
# Global variables
#
#


program = None


#
#
# Constants
#
#


# Instructions and information about them (their corresponding functions)
INSTRUCTIONS = {
        "MOVE":        {"function": Exec.e_move       },
        "CREATEFRAME": {"function": Exec.e_createframe},
        "PUSHFRAME":   {"function": Exec.e_pushframe  },
        "POPFRAME":    {"function": Exec.e_popframe   },
        "DEFVAR":      {"function": Exec.e_defvar     },
        "CALL":        {"function": Exec.e_call       },
        "RETURN":      {"function": Exec.e_return     },
        "PUSHS":       {"function": Exec.e_pushs      },
        "POPS":        {"function": Exec.e_pops       },
        "ADD":         {"function": Exec.e_add        },
        "SUB":         {"function": Exec.e_sub        },
        "MUL":         {"function": Exec.e_mul        },
        "IDIV":        {"function": Exec.e_idiv       },
        "LT":          {"function": Exec.e_lt         },
        "GT":          {"function": Exec.e_gt         },
        "EQ":          {"function": Exec.e_eq         },
        "AND":         {"function": Exec.e_and        },
        "OR":          {"function": Exec.e_or         },
        "NOT":         {"function": Exec.e_not        },
        "INT2CHAR":    {"function": Exec.e_int2char   },
        "STRI2INT":    {"function": Exec.e_stri2int   },
        "READ":        {"function": Exec.e_read       },
        "WRITE":       {"function": Exec.e_write      },
        "CONCAT":      {"function": Exec.e_concat     },
        "STRLEN":      {"function": Exec.e_strlen     },
        "GETCHAR":     {"function": Exec.e_getchar    },
        "SETCHAR":     {"function": Exec.e_setchar    },
        "TYPE":        {"function": Exec.e_type       },
        "LABEL":       {"function": Exec.e_label      },
        "JUMP":        {"function": Exec.e_jump       },
        "JUMPIFEQ":    {"function": Exec.e_jumpifeq   },
        "JUMPIFNEQ":   {"function": Exec.e_jumpifneq  },
        "EXIT":        {"function": Exec.e_exit       },
        "DPRINT":      {"function": Exec.e_dprint     },
        "BREAK":       {"function": Exec.e_break      },
        }


#
#
# MAIN
#
#


if __name__ == "__main__":

    #
    # Parse user-provided arguments
    #

    # Set up the argparser
    argparser = argparse.ArgumentParser(description="A interpret for IPPcode22 represented by a XML file.")
    argparser.add_argument("--source", action="store", help="Source code of a IPPcode22 program in XML format. If not provided, code will be read from standard input")
    argparser.add_argument("--input", action="store", help="Input for the source code implementation. If not provided, input will be forwarded from standard input")
    args = vars(argparser.parse_args())
    if args["source"] == None and args["input"] == None:
        err(0, "Please specify source or input or both")

    # Program input is read from the standard input unless a file is specified
    input_file = sys.stdin
    if args["input"] != None:
        try:
            input_file = open(args["input"], "r")
        except:
            err(11, "Input file provided cannot be read")

    # XML input is read from the standard input unless a file is specified
    xml_file = sys.stdin
    if args["source"] != None:
        try:
            xml_file = open(args["source"], "r")
        except:
            err(11, "XML file provided cannot be read")

    #
    # Get the XML root element and check validity
    #

    try:
        xml_root = ET.ElementTree(ET.fromstring(xml_file.read())).getroot()
    except:
        err(31, "The XML provided is invalid")

    # Check the root tag
    if xml_root.tag != "program":
        err(32, "Missing root element in the XML file")

    # Check the language
    if xml_root.attrib["language"].upper() != "IPPCODE22":
        err(32, "Unrecognized language in the XML file")

    # Check for tags other than the allowed ones (in array elems)
    for elem in xml_root.iter():
        elems = ["instruction", "arg1", "arg2", "arg3", "name", "description"]
        if elem != xml_root and elem.tag not in elems:
            err(32, "Invalid tag in the XML file:", elem.tag)

    #
    # Get all instructions in the XML root element
    #

    instructions = []
    for xml_instr in xml_root:
        if xml_instr.tag != "instruction":
            continue

        # Parse the instruction by creating an object
        try:
            parsed_instr = Instruction(
                xml_instr.attrib["opcode"], 
                xml_instr.attrib["order"]
                )
            instructions.append(parsed_instr)
        # Instruction could not be parsed
        except:
            try:
                err(32, "Invalid instruction #" + xml_instr.attrib["order"])
            except:
                err(32, "Invalid instruction #n/a")

        # Add all the arguments
        for xml_arg in xml_instr:
            parsed_instr.add_arg(xml_arg)
        parsed_instr.check_args()

    #
    # Initialize the program
    #

    program = Program(input_file, instructions)

    #
    # Run instructions until done
    #

    while program.run_next() != False:
        pass
