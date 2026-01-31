import os
import re

class Token:
    def __init__(self, type_, value, line, column):
        self.type = type_
        self.value = value
        self.line = line
        self.column = column

class Tokenizer:
    KEYWORDS = {"type", "end", "dim", "as", "declare", "sub", "function", "#include"}

    def __init__(self, source, filename=""):
        self.source = source
        self.filename = filename
        self.tokens = []
        self._tokenize()

    def _tokenize(self):
        lines = self.source.splitlines()
        for line_idx, line in enumerate(lines, start=1):
            i = 0
            col = 1
            if not line.strip() or line.lstrip().startswith("'"):
                continue
            while i < len(line):
                ch = line[i]
                if ch in " \t":
                    i += 1
                    col += 1
                    continue
                if ch == "'":
                    break
                if ch in '(),':
                    ttype = "COMMA" if ch == "," else ch
                    self.tokens.append(Token(ttype, ch, line_idx, col))
                    i += 1
                    col += 1
                    continue
                if ch == '"':
                    self.tokens.append(Token('"', '"', line_idx, col))
                    i += 1
                    col += 1
                    continue
                if ch.isalpha() or ch == "#":
                    start = i
                    while i < len(line) and (line[i].isalnum() or line[i] in "_#"):
                        i += 1
                    value = line[start:i]
                    ttype = "KEYWORD" if value.lower() in self.KEYWORDS else "IDENT"
                    self.tokens.append(Token(ttype, value, line_idx, col))
                    col += i - start
                    continue
                if ch.isdigit():
                    start = i
                    while i < len(line) and line[i].isdigit():
                        i += 1
                    value = line[start:i]
                    self.tokens.append(Token("NUMBER", value, line_idx, col))
                    col += i - start
                    continue
                i += 1
                col += 1
        self.tokens.append(Token("EOF", "", len(lines) + 1, 1))

    def get_tokens(self):
        return self.tokens

class ASTNode:
    def __init__(self, kind):
        self.kind = kind

class TypeNode(ASTNode):
    def __init__(self, name, fields, methods):
        super().__init__("Type")
        self.name = name
        self.fields = fields
        self.methods = methods

class FieldNode(ASTNode):
    def __init__(self, name, type_name):
        super().__init__("Field")
        self.name = name
        self.type_name = type_name

class MethodNode(ASTNode):
    def __init__(self, name, params, return_type):
        super().__init__("Method")
        self.name = name
        self.params = params
        self.return_type = return_type

class DimNode(ASTNode):
    def __init__(self, names, type_name):
        super().__init__("Dim")
        self.names = names
        self.type_name = type_name

class TypeSymbol:
    def __init__(self, name, fields, methods):
        self.name = name
        self.fields = fields
        self.methods = methods

class VariableSymbol:
    def __init__(self, name, type_name):
        self.name = name
        self.type = type_name

class SymbolTable:
    def __init__(self):
        self.types = {}
        self.variables = {}

    def addType(self, type_symbol):
        self.types[type_symbol.name.lower()] = type_symbol

    def addVariable(self, var_symbol):
        self.variables[var_symbol.name.lower()] = var_symbol

    def getType(self, name):
        if name is None:
            return None
        return self.types.get(name.lower())

    def getVariable(self, name):
        if name is None:
            return None
        return self.variables.get(name.lower())

    def all_types_dict(self):
        result = {}
        for name, ts in self.types.items():
            members = []
            for f in ts.fields:
                members.append({
                    "label": f.name,
                    "insertText": f.name,
                    "detail": f"(Member) {f.name} As {f.type_name}"
                })
            for m in ts.methods:
                members.append({
                    "label": m.name,
                    "insertText": f"{m.name}($1)",
                    "detail": f"(Method) {m.name}"
                })
            result[ts.name] = members
        return result

    def var_to_type_dict(self):
        result = {}
        for name, vs in self.variables.items():
            result[vs.name] = vs.type
        return result

class Parser:
    def __init__(self, tokens, symbol_table, base_path=""):
        self.tokens = tokens
        self.pos = 0
        self.symbol_table = symbol_table
        self.base_path = base_path

    def current(self):
        return self.tokens[self.pos]

    def advance(self):
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return self.current()

    def match_keyword(self, value):
        tok = self.current()
        if tok.type == "KEYWORD" and tok.value.lower() == value.lower():
            self.advance()
            return True
        return False

    def expect_keyword(self, value):
        tok = self.current()
        if tok.type == "KEYWORD" and tok.value.lower() == value.lower():
            self.advance()
            return tok
        raise SyntaxError(f"Expected keyword {value} at line {tok.line}")

    def expect_ident(self):
        tok = self.current()
        if tok.type == "IDENT":
            self.advance()
            return tok
        raise SyntaxError(f"Expected identifier at line {tok.line}")

    def parseBlock(self):
        nodes = []
        while self.current().type != "EOF":
            node = self.parseStatement()
            if node is not None:
                nodes.append(node)
        return nodes

    def parseStatement(self):
        tok = self.current()
        if tok.type == "KEYWORD":
            v = tok.value.lower()
            if v == "#include":
                self.parseInclude()
                return None
            if v == "type":
                return self.parseType()
            if v == "dim":
                return self.parseDim()
        self.advance()
        return None

    def parseInclude(self):
        self.advance()
        tok = self.current()
        if tok.value == '"':
            self.advance()
            path_tok = self.current()
            if path_tok.type in ("IDENT", "KEYWORD"):
                inc_name = path_tok.value
                self.advance()
                if self.current().value == '"':
                    self.advance()
                    full_path = os.path.join(self.base_path, inc_name)
                    if os.path.exists(full_path):
                        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                            code = f.read()
                        tokenizer = Tokenizer(code, full_path)
                        tokens = tokenizer.get_tokens()
                        sub_parser = Parser(tokens, self.symbol_table, os.path.dirname(full_path))
                        sub_parser.parseBlock()
        else:
            while self.current().type != "EOF" and self.current().line == tok.line:
                self.advance()

    def parseType(self):
        self.expect_keyword("type")
        name_tok = self.expect_ident()
        fields = []
        methods = []
        while not (self.current().type == "KEYWORD" and self.current().value.lower() == "end"):
            tok = self.current()
            if tok.type == "KEYWORD" and tok.value.lower() == "declare":
                method = self.parseTypeMethod()
                if method is not None:
                    methods.append(method)
                continue
            if tok.type == "IDENT":
                field = self.parseTypeField()
                if field is not None:
                    fields.append(field)
                continue
            self.advance()
        self.expect_keyword("end")
        self.expect_keyword("type")
        type_node = TypeNode(name_tok.value, fields, methods)
        type_symbol = TypeSymbol(type_node.name, type_node.fields, type_node.methods)
        self.symbol_table.addType(type_symbol)
        return type_node

    def parseTypeField(self):
        name_tok = self.expect_ident()
        if not self.match_keyword("as"):
            return None
        type_tok = self.expect_ident()
        return FieldNode(name_tok.value, type_tok.value)

    def parseTypeMethod(self):
        self.expect_keyword("declare")

        kind_tok = self.current()
        if not (kind_tok.type == "KEYWORD" and kind_tok.value.lower() in ("sub", "function")):
            return None
        self.advance()

        name_tok = self.expect_ident()
        params = []
        return_type = None

        if self.current().value == "(":
            depth = 0
            while True:
                tok = self.current()

                if tok.value == "(":
                    depth += 1
                elif tok.value == ")":
                    depth -= 1
                    self.advance()
                    if depth == 0:
                        break

                self.advance()

                if tok.type == "EOF":
                    break

        if kind_tok.value.lower() == "function":
            if self.match_keyword("as"):
                rt_tok = self.expect_ident()
                return_type = rt_tok.value

        return MethodNode(name_tok.value, params, return_type)


    def parseDim(self):
        self.expect_keyword("dim")
        names = []
        type_name = None
        if self.match_keyword("as"):
            type_tok = self.expect_ident()
            type_name = type_tok.value
            while True:
                tok = self.current()
                if tok.type in ("IDENT", "KEYWORD"):
                    names.append(tok.value)
                    self.advance()
                else:
                    break
                if self.current().type == "COMMA":
                    self.advance()
                    continue
                break
        else:
            while True:
                tok = self.current()
                if tok.type in ("IDENT", "KEYWORD"):
                    names.append(tok.value)
                    self.advance()
                else:
                    break
                if self.current().type == "COMMA":
                    self.advance()
                    continue
                break
            if self.match_keyword("as"):
                type_tok = self.expect_ident()
                type_name = type_tok.value
        dim_node = DimNode(names, type_name)
        if type_name is not None:
            for n in names:
                vs = VariableSymbol(n, type_name)
                self.symbol_table.addVariable(vs)
        return dim_node

def resolveVariableType(symbol_table, name):
    var = symbol_table.getVariable(name)
    if var is None:
        return None
    return var.type

def getMembersOfType(symbol_table, type_name):
    t = symbol_table.getType(type_name)
    if t is None:
        return []
    members = []
    for f in t.fields:
        members.append({
            "label": f.name,
            "insertText": f.name,
            "detail": f"(Member) {f.name} As {f.type_name}"
        })
    for m in t.methods:
        members.append({
            "label": m.name,
            "insertText": f"{m.name}($1)",
            "detail": f"(Method) {m.name}"
        })
    return members

def provideCompletions(symbol_table, text, position):
    line = text.splitlines()[position["line"]]
    prefix = line[:position["character"]]
    m = re.search(r"(\w+)\.\s*$", prefix)
    if not m:
        return []
    var_name = m.group(1)
    tname = resolveVariableType(symbol_table, var_name)
    if tname is None:
        return []
    return getMembersOfType(symbol_table, tname)

def provideHover(symbol_table, text, position):
    line = text.splitlines()[position["line"]]
    col = position["character"]
    start = col
    while start > 0 and (start - 1) < len(line) and line[start - 1].isalnum() or (start - 1) < len(line) and line[start - 1] == "_":
        start -= 1
    end = col
    while end < len(line) and (line[end].isalnum() or line[end] == "_"):
        end += 1
    name = line[start:end].strip()
    if not name:
        return None
    var = symbol_table.getVariable(name)
    if var is not None:
        return f"{var.name} As {var.type}"
    t = symbol_table.getType(name)
    if t is not None:
        return f"Type {t.name}"
    return None

def provideDiagnostics(ast_nodes):
    return []

def parse_source_with_includes(source_code, current_file_path=""):
    base_path = os.path.dirname(current_file_path) if current_file_path else ""
    tokenizer = Tokenizer(source_code, current_file_path)
    tokens = tokenizer.get_tokens()
    symbols = SymbolTable()
    parser = Parser(tokens, symbols, base_path)
    ast = parser.parseBlock()
    return ast, symbols
