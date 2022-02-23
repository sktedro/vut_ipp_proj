# interpret.py
# Author: Patrik Skaloš
# Warning: This script is not to be imported as a module

import re
import argparse
import xml.etree.ElementTree as ET
import sys
import operator

#
#
# Miscellaneous functions
#
#


# Print an error and exit if an exit code was provided
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
        self.labels = {}
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

                name = instr.args[0].symb_val()

                # Make sure a label with that name doesn't already exist
                if name in self.labels:
                    err(52, "Label name " + name + " used twice")

                # Create the new label
                self.labels[name] = instr.order


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
        operand1 = int(args[1].symb_val())
        operand2 = int(args[2].symb_val())
        program.symtab.define(
                args[0], 
                "int", 
                str(operator(operand1, operand2))
                )

    # Does a binary relational operation specified by operator
    # args[0] = args[1] <operator> args[2]
    def bool_relational_op(args, operator):
        # TODO EQ cannot compare nil with nil
        # TODO relation between booleans?
        if args[1].symb_type() == args[2].symb_type() == "int":
            operand1 = int(args[1].symb_val())
            operand2 = int(args[2].symb_val())
        #  elif args[1].symb_type() == args[2].symb_type() == "bool":
            #  operand1 = bool(args[1].symb_val())
            #  operand2 = bool(args[2].symb_val())
        else:
            operand1 = args[1].symb_val()
            operand2 = args[2].symb_val()
        code_err(None, str(operand1) + str(operator) + str(operand2) + "=" + str(operator(operand1, operand2)).lower())
        program.symtab.define(
                args[0], 
                "bool", 
                str(operator(operand1, operand2)).lower()
                )
    # Does a binary boolean operation specified by operator
    # args[0] = args[1] <operator> args[2]
    def bool_binary_op(args, operator):
        operand1 = args[1].symb_val() == "true"
        operand2 = args[2].symb_val() == "true"
        program.symtab.define(
                args[0], 
                "bool", 
                str(operator(operand1, operand2)).lower()
                )

    # MOVE
    def e_move(args):
        program.symtab.define(
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
        # Move LF to TF by popping from LFs
        try:
            program.symtab.tf = program.symtab.lfs.pop()
        except:
            code_err(55, "Cannot pop a temporary frame since none exists")

    # DEFVAR
    def e_defvar(args):
        program.symtab.declare(args[0])

    # CALL
    def e_call(args):
        program.return_stack.append(program.prev_order)
        Exec.e_jump(args)

    # RETURN
    def e_return(args):
        try:
            program.jump_after_order(program.return_stack[-1])
            program.return_stack.pop()
        except:
            code_err(56, "Cannot return from a call, call stack is empty")

    # PUSHS
    def e_pushs(args):
        arg_type = args[0].type
        arg_val = args[0].symb_val()
        program.data_stack.append({"type": arg_type, "val": arg_val})

    # POPS
    def e_pops(args):
        try:
            popped_item = program.data_stack.pop()
        except:
            code_err(56, "Cannot pop from an empty stack")
        program.symtab.define(
                args[0], 
                popped_item["type"], 
                popped_item["val"]
                )
        

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

    # Binary relational operations:
    # LT GT EQ 
    def e_lt(args):
        Exec.bool_relational_op(args, operator.__lt__)
    def e_gt(args):
        Exec.bool_relational_op(args, operator.__gt__)
    def e_eq(args):
        Exec.bool_relational_op(args, operator.__eq__)

    # Binary boolean operations:
    # AND OR
    def e_and(args):
        Exec.bool_binary_op(args, operator.__and__)
    def e_or(args):
        Exec.bool_binary_op(args, operator.__or__)

    # NOT
    def e_not(args):
        operand = args[1].symb_val() == "true"
        program.symtab.define(
                args[0], 
                "bool", 
                str(not operand).lower()
                )

    # INT2CHAR
    def e_int2char(args):
        try:
            result = chr(int(args[1].symb_val()))
        except:
            code_err(58, "Cannot convert integer to character: out of range")
        program.symtab.define(
                args[0], 
                "string", 
                result
                )

    # STR2INT
    def e_stri2int(args):
        index = int(args[2].symb_val())
        string = args[1].symb_val()
        if not 0 <= index < len(string):
            code_err(58, "Cannot convert character to integer: out of range")
        program.symtab.define(
                args[0], 
                "int", 
                str(ord(string[index]))
                )

    # READ
    def e_read(args):
        # Read from the input file
        line = program.input_file.readline()
        try:
            # If the line is empty (EOF):
            if line == "":
                raise Exception("Missing input")
            # Drop the newline at the end if it exists
            if line[-1] == "\n":
                line = line[: -1] 
            # Parse the input
            if args[1].val == "int":
                line = "int@" + str(int(line))
            elif args[1].val == "string":
                line = "string@" + line
            elif args[1].val == "bool":
                code_err(None, line)
                line = "bool@true" if line.upper() == "TRUE" else "bool@false"
        except:
            line = "nil@nil"
        program.symtab.define(
                args[0], 
                line.split("@", 1)[0], 
                line.split("@", 1)[1]
                )

    # WRITE
    def e_write(args):
        if args[0].symb_type() != "nil":
            print(args[0].symb_val(), end="")

    # CONCAT 
    def e_concat(args):
        program.symtab.define(
                args[0], 
                "string", 
                args[1].symb_val() + args[2].symb_val()
                )

    # STRLEN
    def e_strlen(args):
        program.symtab.define(
                args[0], 
                "int", 
                len(args[1].symb_val())
                )

    # GETCHAR
    def e_getchar(args):
        string = args[1].symb_val()
        index = int(args[2].symb_val())
        if not 0 <= index < len(string):
            code_err(58, "GETCHAR: index out of range")
        program.symtab.define(
                args[0], 
                "string", 
                string[int(index)]
                )

    # SETCHAR
    def e_setchar(args):
        if len(args[2].symb_val()) < 1:
            code_err(58, "SETCHAR: replacement string empty")
        if not 0 <= int(args[1].symb_val()) < len(args[0].symb_val()):
            code_err(58, "SETCHAR: index out of range")
        char = args[2].symb_val()[0]
        string = args[0].symb_val()
        index = int(args[1].symb_val())
        program.symtab.define(
                args[0], 
                "string", 
                string[: index] + char + string[index + 1: ]
                )

    # TYPE
    def e_type(args):
        # Get the data type - if symb_type fails, the variable is declared but
        # not defined and we should return an empty string
        try:
            symb_type = args[1].symb_type()
        except:
            symb_type = ""
        program.symtab.define(
                args[0], 
                "string", 
                symb_type
                )

    # LABEL
    def e_label(args):
        pass # Pass, since the labels are already in the program.labels array

# TODO "eq" (not here but in INSTRUCTIONS)
    # JUMP
    def e_jump(args):
        program.jump_after_order(program.labels[args[0].symb_val()])

    # JUMPIFEQ
    def e_jumpifeq(args):
        if (args[1].symb_type() == "nil"
                or args[2].symb_type() == "nil"
                or args[1].symb_type() == args[2].symb_type()):
            if args[1].symb_val() == args[2].symb_val():
                Exec.e_jump([args[0]])
        else:
            code_err(53, "JUMPIFEQ: data types not compatible")

    # JUMPIFNEQ
    def e_jumpifneq(args):
        if (args[1].symb_type() == "nil"
                or args[2].symb_type() == "nil"
                or args[1].symb_type() == args[2].symb_type()):
            if args[1].symb_val() != args[2].symb_val():
                Exec.e_jump([args[0]])
        else:
            code_err(53, "JUMPIFNEQ: data types not compatible")

    # EXIT
    def e_exit(args):
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
#   order of the argument
#   type: "var", "string", "label", "int", ...
#   val: raw text of the argument
class Argument:
    def __init__(self, arg_xml):
        # Argument tag can only be "arg1", "arg2" or "arg3"
        if re.search("^arg[123]$", arg_xml.tag) == None:
            code_err(32, "Received an argument with invalid tag")

        # Type of the argument needs to be specified
        if "type" not in arg_xml.attrib:
            code_err(31, "Received an argument without type specified")

        self.order = int(arg_xml.tag[-1])
        self.type = arg_xml.attrib["type"]
        self.val = arg_xml.text

        if self.type == "string":
            # If it is an empty string, arg_xml.text will be None!
            if self.val == None:
                self.val = ""
            # Convert all escaped sequences to normal characters
            while re.search("\\\(\\d{1,3})", self.val) != None:
                match = re.search("\\\(\\d{1,3})", self.val)
                sequence = self.val[match.span()[0]: match.span()[1]]
                self.val = self.val.replace(sequence, chr(int(sequence[1: ])))

        # Check validity of literals (eg. bool@haha, int@a, nil@1 are invalid)
        if self.type == "int" and re.search("^[+|-]?\d+$", self.val) == None:
            code_err(53, "Invalid integer literal")
        if self.type == "bool" and self.val not in ["true", "false"]:
            code_err(53, "Invalid bool literal")
        if self.type == "nil" and self.val != "nil":
            code_err(53, "Nil data type can only contain value nil")


    # Get symbol value (from the symtable it if is a variable)
    def symb_val(self):
        if self.type == "var":
            return program.symtab.get(self.val)["val"]
        else:
            return self.val


    # Get symbol data type (from the symtable it if is a variable)
    def symb_type(self):
        if self.type == "var":
            return program.symtab.get(self.val)["type"]
        else:
            return self.type

# TODO refactored to this point

# Class defining an instruction, consisting of:
#   order (of the instruction)
#   opcode (name of the instruction)
#   args (array of Argument objects)
class Instruction:
    def __init__(self, opcode, order):

        # Order must be a number
        if re.search("^\d+$", order) == None:
            err(32, "Order of an instruction #n/a is not a number")

        # Order must be above 0
        if int(order) < 1:
            err(32, "Order of an instruction #" + order + " is lower than 1")

        # Check for invalid opcode
        if not opcode.upper() in INSTRUCTIONS:
            err(32, "Invalid opcode:", opcode)

        self.order = int(order)
        self.opcode = opcode.upper()
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


    # Run the instruction
    def run(self):

        # Check the amount of arguments
        if len(INSTRUCTIONS[self.opcode]["types"]) != len(self.args):
            err(53, "Wrong arguments amount of instruction #" + str(self.order))

        # Check if arguments are defined (not just declared)
        for i in range(len(self.args)):
            req = INSTRUCTIONS[self.opcode]["requirements"][i]
            # Skip if there's no requirement
            if req not in ["declared", "defined"]:
                continue
            # If the argument is a variable, dig into the symtab to get the val
            if self.args[i].type == "label":
                name = self.args[i].val
                if not name in program.labels:
                    code_err(52, "Label " + name + " does not exist")
            elif self.args[i].type == "var":
                var = self.args[i].val
                if req == "declared" and not program.symtab.declared(var):
                    code_err(54, "Variable " + var + " not declared")
                elif req == "defined":
                    if not program.symtab.declared(var):
                        code_err(54, "Variable " + var + " not declared")
                    if not program.symtab.defined(var):
                        code_err(56, "Variable " + var + " not defined")

        # Check argument types
        for i in range(len(self.args)):
            req_type = INSTRUCTIONS[self.opcode]["types"][i]
            got_type = self.args[i].type
            # Skip if we don't care about the type
            if req_type == "any":
                continue
            # A symbol can be a variable or a literal
            elif req_type == "symb":
                if got_type not in ["var", "int", "string", "bool", "nil"]:
                    code_err(53, "Wrong argument type")
            # Otherwise the types must match exactly
            else:
                if req_type != got_type:
                    code_err(53, "Wrong argument type")

        #  Check argument data types
        for i in range(len(self.args)):
            req_type = INSTRUCTIONS[self.opcode]["data_types"][i]
            got_type = self.args[i].type
            # Skip if we don't care or they need to be equal
            if req_type == "any" or req_type == "eq":
                continue
            # If the argument is a variable, dig into the symtab to get the val
            if got_type == "var":
                got_type = self.args[i].symb_type()
            # Check if the types match exactly
            if req_type != got_type:
                code_err(53, "Wrong argument data type: requires " 
                        + req_type + " but received " + got_type)
        # If they need to be equal, make sure they are
        if "eq" in INSTRUCTIONS[self.opcode]["data_types"]:
            types = INSTRUCTIONS[self.opcode]["data_types"]
            indices = [i for i in range(len(types)) if types[i] == "eq"]
            base_type = self.args[indices[0]].symb_type()
            for i in indices[1: ]:
                comp_type = self.args[i].symb_type()
                # Exception: LT and GT can't compare nils
                if self.opcode in ["LT", "GT"] and "nil" in [comp_type, base_type]:
                    code_err(53, "LT/GT instruction can't compare nils")
                # Exception: EQ instruction which CAN compare with nil
                if self.opcode == "EQ" and "nil" in [comp_type, base_type]:
                    continue
                # Otherwise if the types don't match, throw an error
                if comp_type != base_type:
                    code_err(53, "Wrong argument data types: "
                            + comp_type
                            + " should be the same as "
                            + base_type)

        # Execute the instruction
        INSTRUCTIONS[self.opcode]["function"](self.args)


class SymTab:
    def __init__(self):
        self.lfs = []
        self.gf = {}
        self.tf = None

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

    def declare(self, var):
        name = self.get_name(var)
        frame = self.get_frame(var)
        if name in frame:
            code_err(52, "Redeclaration of variable " + name)
        frame[name] = {
                "declared": True,
                "defined": False,
                "type": None,
                "val": None
                }

    def declared(self, var):
        name = self.get_name(var)
        frame = self.get_frame(var)
        if name in frame and frame[name]["declared"] == True:
            return True
        else:
            return False

    def define(self, var, literal_type, literal):
        name = self.get_name(var)
        frame = self.get_frame(var)
        frame[name] = {
                "declared": True,
                "defined": True,
                "type": literal_type,
                "val": literal
                }

    def defined(self, var):
        name = self.get_name(var)
        frame = self.get_frame(var)
        if name in frame and frame[name]["defined"] == True:
            return True
        else:
            return False

    def get(self, var):
        if self.defined(var):
            frame = self.get_frame(var)
            name = self.get_name(var)
            return frame[name]
        else:
            return None


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


# Instructions and information about them:
# their corresponding functions and data types of their arguments
INSTRUCTIONS = {
        "MOVE":        {
            "function": Exec.e_move,       
            "types":      ["var", "symb"],
            "data_types": ["any", "any"],
            "requirements": ["declared", "defined"]},
        "CREATEFRAME": {
            "function": Exec.e_createframe,
            "types":      [],
            "data_types": [],
            "requirements": []},
        "PUSHFRAME":   {
            "function": Exec.e_pushframe,  
            "types":      [],
            "data_types": [],
            "requirements": []},
        "POPFRAME":    {
            "function": Exec.e_popframe,   
            "types":      [],
            "data_types": [],
            "requirements": []},
        "DEFVAR":      {
            "function": Exec.e_defvar,     
            "types":      ["var"],
            "data_types": ["any"],
            "requirements": ["none"]},
        "CALL":        {
            "function": Exec.e_call,       
            "types":      ["label"],
            "data_types": ["any"],
            "requirements": ["defined"]},
        "RETURN":      {
            "function": Exec.e_return,     
            "types":      [],
            "data_types": [],
            "requirements": []},
        "PUSHS":       {
            "function": Exec.e_pushs,      
            "types":      ["symb"],
            "data_types": ["any"],
            "requirements": ["defined"]},
        "POPS":        {
            "function": Exec.e_pops,       
            "types":      ["var"],
            "data_types": ["any"],
            "requirements": ["declared"]},
        "ADD":         {
            "function": Exec.e_add,        
            "types":      ["var", "symb", "symb"],
            "data_types": ["any", "int", "int"],
            "requirements": ["declared", "defined", "defined"]},
        "SUB":         {
            "function": Exec.e_sub,        
            "types":      ["var", "symb", "symb"],
            "data_types": ["any", "int", "int"],
            "requirements": ["declared", "defined", "defined"]},
        "MUL":         {
            "function": Exec.e_mul,        
            "types":      ["var", "symb", "symb"],
            "data_types": ["any", "int", "int"],
            "requirements": ["declared", "defined", "defined"]},
        "IDIV":        {
            "function": Exec.e_idiv,       
            "types":      ["var", "symb", "symb"],
            "data_types": ["any", "int", "int"],
            "requirements": ["declared", "defined", "defined"]},
        "LT":          {
            "function": Exec.e_lt,         
            "types":      ["var", "symb", "symb"],
            "data_types": ["any", "eq", "eq"],
            "requirements": ["declared", "defined", "defined"]},
        "GT":          {
            "function": Exec.e_gt,         
            "types":      ["var", "symb", "symb"],
            "data_types": ["any", "eq", "eq"],
            "requirements": ["declared", "defined", "defined"]},
        "EQ":          {
            "function": Exec.e_eq,         
            "types":      ["var", "symb", "symb"],
            "data_types": ["any", "eq", "eq"],
            "requirements": ["declared", "defined", "defined"]},
        "AND":         {
            "function": Exec.e_and,        
            "types":      ["var", "symb", "symb"],
            "data_types": ["any", "bool", "bool"],
            "requirements": ["declared", "defined", "defined"]},
        "OR":          {
            "function": Exec.e_or,         
            "types":      ["var", "symb", "symb"],
            "data_types": ["any", "bool", "bool"],
            "requirements": ["declared", "defined", "defined"]},
        "NOT":         {
            "function": Exec.e_not,        
            "types":      ["var", "symb"],
            "data_types": ["any", "bool"],
            "requirements": ["declared", "defined"]},
        "INT2CHAR":    {
            "function": Exec.e_int2char,   
            "types":      ["var", "symb"],
            "data_types": ["any", "int"],
            "requirements": ["declared", "defined"]},
        "STRI2INT":    {
            "function": Exec.e_stri2int,   
            "types":      ["var", "symb", "symb"],
            "data_types": ["any", "string", "int"],
            "requirements": ["declared", "defined", "defined"]},
        "READ":        {
            "function": Exec.e_read,       
            "types":      ["var", "type"],
            "data_types": ["any", "any"],
            "requirements": ["declared", "defined"]},
        "WRITE":       {
            "function": Exec.e_write,      
            "types":      ["symb"],
            "data_types": ["any"],
            "requirements": ["defined"]},
        "CONCAT":      {
            "function": Exec.e_concat,     
            "types":      ["var", "symb", "symb"],
            "data_types": ["any", "string", "string"],
            "requirements": ["declared", "defined", "defined"]},
        "STRLEN":      {
            "function": Exec.e_strlen,     
            "types":      ["var", "symb"],
            "data_types": ["any", "string"],
            "requirements": ["declared", "defined"]},
        "GETCHAR":     {
            "function": Exec.e_getchar,    
            "types":      ["var", "symb", "symb"],
            "data_types": ["any", "string", "int"],
            "requirements": ["declared", "defined", "defined"]},
        "SETCHAR":     {
            "function": Exec.e_setchar,    
            "types":      ["var", "symb", "symb"],
            "data_types": ["string", "int", "string"],
            "requirements": ["defined", "defined", "defined"]},
        "TYPE":        {
            "function": Exec.e_type,       
            "types":      ["var", "symb"],
            "data_types": ["any", "any"],
            "requirements": ["declared", "declared"]},
        "LABEL":       {
            "function": Exec.e_label,      
            "types":      ["label"],
            "data_types": ["any"],
            "requirements": ["none"]},
        "JUMP":        {
            "function": Exec.e_jump,       
            "types":      ["label"],
            "data_types": ["any"],
            "requirements": ["defined"]},
        "JUMPIFEQ":    {
            "function": Exec.e_jumpifeq,   
            "types":      ["label", "symb", "symb"],
            "data_types": ["any", "any", "any"],
            "requirements": ["defined", "defined", "defined"]},
        "JUMPIFNEQ":   {
            "function": Exec.e_jumpifneq,  
            "types":      ["label", "symb", "symb"],
            "data_types": ["any", "any", "any"],
            "requirements": ["defined", "defined", "defined"]},
        "EXIT":        {
            "function": Exec.e_exit,       
            "types":      ["symb"],
            "data_types": ["int"],
            "requirements": ["defined"]},
        "DPRINT":      {
            "function": Exec.e_dprint,     
            "types":      ["symb"],
            "data_types": ["any"],
            "requirements": ["defined"]},
        "BREAK":       {
            "function": Exec.e_break,      
            "types":      [],
            "data_types": [],
            "requirements": []},
        }
#  INSTRUCTIONS = {
        #  "MOVE":        {
            #  "function": Exec.e_move,       
            #  "types":      ["var", "symb"],
            #  "data_types": [["any"], ["any"]],
            #  "requirements": ["declared", "defined"]},
        #  "CREATEFRAME": {
            #  "function": Exec.e_createframe,
            #  "types":      [],
            #  "data_types": [],
            #  "requirements": []},
        #  "PUSHFRAME":   {
            #  "function": Exec.e_pushframe,  
            #  "types":      [],
            #  "data_types": [],
            #  "requirements": []},
        #  "POPFRAME":    {
            #  "function": Exec.e_popframe,   
            #  "types":      [],
            #  "data_types": [],
            #  "requirements": []},
        #  "DEFVAR":      {
            #  "function": Exec.e_defvar,     
            #  "types":      ["var"],
            #  "data_types": [["any"]],
            #  "requirements": ["none"]},
        #  "CALL":        {
            #  "function": Exec.e_call,       
            #  "types":      ["label"],
            #  "data_types": [["any"]],
            #  "requirements": ["defined"]},
        #  "RETURN":      {
            #  "function": Exec.e_return,     
            #  "types":      [],
            #  "data_types": [],
            #  "requirements": []},
        #  "PUSHS":       {
            #  "function": Exec.e_pushs,      
            #  "types":      ["symb"],
            #  "data_types": [["any"]],
            #  "requirements": ["defined"]},
        #  "POPS":        {
            #  "function": Exec.e_pops,       
            #  "types":      ["var"],
            #  "data_types": [["any"]],
            #  "requirements": ["declared"]},
        #  "ADD":         {
            #  "function": Exec.e_add,        
            #  "types":      ["var", "symb", "symb"],
            #  "data_types": [["any"], ["int"], ["int"]],
            #  "requirements": ["declared", "defined", "defined"]},
        #  "SUB":         {
            #  "function": Exec.e_sub,        
            #  "types":      ["var", "symb", "symb"],
            #  "data_types": [["any"], ["int"], ["int"]],
            #  "requirements": ["declared", "defined", "defined"]},
        #  "MUL":         {
            #  "function": Exec.e_mul,        
            #  "types":      ["var", "symb", "symb"],
            #  "data_types": [["any"], ["int"], ["int"]],
            #  "requirements": ["declared", "defined", "defined"]},
        #  "IDIV":        {
            #  "function": Exec.e_idiv,       
            #  "types":      ["var", "symb", "symb"],
            #  "data_types": [["any"], ["int"], ["int"]],
            #  "requirements": ["declared", "defined", "defined"]},
        #  "LT":          {
            #  "function": Exec.e_lt,         
            #  "types":      ["var", "symb", "symb"],
            #  "data_types": [["any"], ["eq"], ["eq"]],
            #  "requirements": ["declared", "defined", "defined"]},
        #  "GT":          {
            #  "function": Exec.e_gt,         
            #  "types":      ["var", "symb", "symb"],
            #  "data_types": [["any"], ["eq"], ["eq"]],
            #  "requirements": ["declared", "defined", "defined"]},
        #  "EQ":          {
            #  "function": Exec.e_eq,         
            #  "types":      ["var", "symb", "symb"],
            #  "data_types": [["any"], ["eq"], ["eq"]],
            #  "requirements": ["declared", "defined", "defined"]},
        #  "AND":         {
            #  "function": Exec.e_and,        
            #  "types":      ["var", "symb", "symb"],
            #  "data_types": [["any"], ["bool"], ["bool"]],
            #  "requirements": ["declared", "defined", "defined"]},
        #  "OR":          {
            #  "function": Exec.e_or,         
            #  "types":      ["var", "symb", "symb"],
            #  "data_types": [["any"], ["bool"], ["bool"]],
            #  "requirements": ["declared", "defined", "defined"]},
        #  "NOT":         {
            #  "function": Exec.e_not,        
            #  "types":      ["var", "symb"],
            #  "data_types": [["any"], ["bool"]],
            #  "requirements": ["declared", "defined"]},
        #  "INT2CHAR":    {
            #  "function": Exec.e_int2char,   
            #  "types":      ["var", "symb"],
            #  "data_types": [["any"], ["int"]],
            #  "requirements": ["declared", "defined"]},
        #  "STRI2INT":    {
            #  "function": Exec.e_stri2int,   
            #  "types":      ["var", "symb", "symb"],
            #  "data_types": [["any"], ["string"], ["int"]],
            #  "requirements": ["declared", "defined", "defined"]},
        #  "READ":        {
            #  "function": Exec.e_read,       
            #  "types":      ["var", "type"],
            #  "data_types": [["any"], ["any"]],
            #  "requirements": ["declared", "defined"]},
        #  "WRITE":       {
            #  "function": Exec.e_write,      
            #  "types":      ["symb"],
            #  "data_types": [["any"]],
            #  "requirements": ["defined"]},
        #  "CONCAT":      {
            #  "function": Exec.e_concat,     
            #  "types":      ["var", "symb", "symb"],
            #  "data_types": [["any"], ["string"], ["string"]],
            #  "requirements": ["declared", "defined", "defined"]},
        #  "STRLEN":      {
            #  "function": Exec.e_strlen,     
            #  "types":      ["var", "symb"],
            #  "data_types": [["any"], ["string"]],
            #  "requirements": ["declared", "defined"]},
        #  "GETCHAR":     {
            #  "function": Exec.e_getchar,    
            #  "types":      ["var", "symb", "symb"],
            #  "data_types": [["any"], ["string"], ["int"]],
            #  "requirements": ["declared", "defined", "defined"]},
        #  "SETCHAR":     {
            #  "function": Exec.e_setchar,    
            #  "types":      ["var", "symb", "symb"],
            #  "data_types": [["string"], ["int"], ["string"]],
            #  "requirements": ["defined", "defined", "defined"]},
        #  "TYPE":        {
            #  "function": Exec.e_type,       
            #  "types":      ["var", "symb"],
            #  "data_types": [["any"], ["any"]],
            #  "requirements": ["declared", "declared"]},
        #  "LABEL":       {
            #  "function": Exec.e_label,      
            #  "types":      ["label"],
            #  "data_types": [["any"]],
            #  "requirements": ["none"]},
        #  "JUMP":        {
            #  "function": Exec.e_jump,       
            #  "types":      ["label"],
            #  "data_types": [["any"]],
            #  "requirements": ["defined"]},
        #  "JUMPIFEQ":    {
            #  "function": Exec.e_jumpifeq,   
            #  "types":      ["label", "symb", "symb"],
            #  "data_types": [["any"], ["any"], ["any"]],
            #  "requirements": ["defined", "defined", "defined"]},
        #  "JUMPIFNEQ":   {
            #  "function": Exec.e_jumpifneq,  
            #  "types":      ["label", "symb", "symb"],
            #  "data_types": [["any"], ["any"], ["any"]],
            #  "requirements": ["defined", "defined", "defined"]},
        #  "EXIT":        {
            #  "function": Exec.e_exit,       
            #  "types":      ["symb"],
            #  "data_types": [["int"]],
            #  "requirements": ["defined"]},
        #  "DPRINT":      {
            #  "function": Exec.e_dprint,     
            #  "types":      ["symb"],
            #  "data_types": [["any"]],
            #  "requirements": ["defined"]},
        #  "BREAK":       {
            #  "function": Exec.e_break,      
            #  "types":      [],
            #  "data_types": [],
            #  "requirements": []},
        #  }



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

        # Check if opcode and order are both provided
        if "opcode" not in xml_instr.attrib or "order" not in xml_instr.attrib:
            if "order" in xml_instr.attrib:
                err(32, "Invalid instruction #" + xml_instr.attrib["order"])
            else:
                err(32, "Invalid instruction #n/a")

        # Parse the instruction by creating an object
        parsed_instr = Instruction(
            xml_instr.attrib["opcode"], 
            xml_instr.attrib["order"]
            )
        instructions.append(parsed_instr)

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
