"""Parser for Leaf."""

from tokens import *
from leaf_ast import *


class Parser:

    def __init__(self, lexer):
        self.lexer = lexer
        self.current_token = self.lexer.next_token()

    def consume_token(self, token_type):
        if self.current_token.type == token_type:
            # print('                  old token', self.current_token)
            self.current_token = self.lexer.next_token()
            # print('                  new token', self.current_token)
        else:
            self.raise_error(token_type=token_type,
                             received=self.current_token.type)

    def raise_error(self, token=None, *, token_type=None, received=None):
        # print('CURRENT TOKEN:', self.current_token)
        if token:
            raise SyntaxError('Invalid syntax: {} ({})'
                              .format(repr(token.value), token.type))
        elif token_type and received:
            raise SyntaxError('Invalid syntax: expected {}, got {}'
                              .format(token_type, received))
        else:
            raise SyntaxError('Invalid syntax')

    def program(self):
        return self.statement_list()

##    def compound_statement(self):
##        root = CompoundStatement()
##        for node in self.statement_list():
##            root.children.append(node)
##
##        return root

    def statement_list(self):
        root = StatementList()
        root.children.append(self.statement())
        while self.current_token.type == NEWLINE:
            self.consume_token(NEWLINE)
            root.children.append(self.statement())

        return root

    def statement(self):
        if self.current_token.type == IDENTIFIER:
            node = self.assign_statement()

        elif self.current_token.type in (STR_TYPE, NUM_TYPE):
            node = self.variable_declaration()

        elif self.current_token.type in (ADD, SUB, LPAREN, NUM, STR):
            #                   unary ops ^^  ^^        num ^^
            #                            paren expr ^^    string ^^
            node = self.expression()

        elif self.current_token.type in builtin_functions:
            node = self.builtin_function()

        else:
            node = self.empty()

        return node

    def assign_statement(self):
        left = self.variable()

        token = self.current_token
        self.consume_token(ASSIGN)

        return Assign(left_node=left,
                      operator=token,
                      right_node=self.expression())

    def variable_declaration(self):
        pass   # add var dec

    def builtin_function(self):
        token = self.current_token
        function = builtin_functions[token.type]

        self.consume_token(function.name)
        self.consume_token(LBRACKET)

        if function.arbitrary:
            args = self.arbitrary_argument_list()

        else:
            args = []
            for i, arg_name in enumerate(function.arg_names):
                try:
                    args.append(self.expression())
                    if i < len(function.arg_names) - 1:
                        self.consume_token(COMMA)
                except SyntaxError as e:
                    raise SyntaxError('Invalid syntax: expected argument {}: {}'
                                      .format(i + 1, arg_name))

        self.consume_token(RBRACKET)

        modifiers = self.modifier_list()  # dict
        for mod_name in modifiers.keys():
            if mod_name not in function.modifiers:
                raise SyntaxError('Invalid syntax: unexpected modifier {} ({})'
                                  .format(mod_name, modifiers[mod_name]))

        return FunctionCall(function  = function,
                            args      = args,
                            modifiers = modifiers)

    def arbitrary_argument_list(self):
        try:
            results = [self.expression()]
        except SyntaxError:  # no expression found, got [
            results = []
        while self.current_token.type == COMMA:
            self.consume_token(COMMA)
            results.append(self.expression())

        return results

    def modifier_list(self):
        results = {}
        while self.current_token.type == TILDE:
            self.consume_token(TILDE)
            modifier = self.assign_statement()

            name = modifier.left.value    # Variable.value
            value = modifier.right.value  # expression()
            results[name] = value

        return results

    def empty(self):
        return Empty()

    def variable(self):
        node = Variable(self.current_token)
        self.consume_token(IDENTIFIER)
        return node

    def if_statement(self):
        pass

    def indented_statement_list(self):
        pass

    def expression(self):
        return self.comparison()

    def comparison(self):
        node = self.addition()
        while self.current_token.type in (EQUAL, N_EQUAL, L_EQUAL,
                                          G_EQUAL, LESS, GREATER):
            token = self.current_token
            self.consume_token(token.type)

            node = BinaryOperation(left_node  = node,
                                   operator   = token,
                                   right_node = self.addition())
        return node

    def addition(self):
        node = self.multiplication()
        while self.current_token.type in (ADD, SUB):
            token = self.current_token
            self.consume_token(token.type)

            node = BinaryOperation(left_node  = node,
                                   operator   = token,
                                   right_node = self.multiplication())
        return node

    def multiplication(self):
        node = self.unary()
        while self.current_token.type in (MUL, DIV, FLOORDIV):
            token = self.current_token
            self.consume_token(token.type)

            node = BinaryOperation(left_node  = node,
                                   operator   = token,
                                   right_node = self.unary())

        return node

    def unary(self):
        token = self.current_token
        if token.type in (ADD, SUB):
            self.consume_token(token.type)
            return UnaryOperation(operator   = token,
                                  expression = self.unary())

        elif token.type in (NUM, STR, IDENTIFIER, LPAREN):
            return self.exponent()

        else:
            self.raise_error(token)

    def exponent(self):
        node = self.atom()
        while self.current_token.type == POWER:
            token = self.current_token
            self.consume_token(token.type)

            node = BinaryOperation(left_node  = node,
                                   operator   = token,
                                   right_node = self.exponent())
        return node

    def atom(self):
        token = self.current_token
        if token.type == NUM:
            self.consume_token(NUM)
            return Number(token)

        elif token.type == STR:
            self.consume_token(STR)
            return String(token)

        elif token.type == LPAREN:
            return self.paren_expr()

        elif token.type == IDENTIFIER:
            return self.variable()

        else:
            self.raise_error(token)

    def paren_expr(self):
        self.consume_token(LPAREN)
        node = self.expression()
        self.consume_token(RPAREN)
        return node

    def parse(self):
        node = self.program()
        if self.current_token.type not in (EOF, NEWLINE):
            self.raise_error(self.current_token)

        return node
