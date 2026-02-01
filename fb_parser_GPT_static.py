import os
import re

# === AI_INSERT_POINT:IMPORTS ===

class Token:
    def __init__(self, type_, value, line, column):
        self.type = type_
        self.value = value
        self.line = line
        self.column = column

class KeywordRegistry:
    """Keskitetty rekisteri kaikille avainsanoille ja niiden käsittelijöille."""
    def __init__(self):
        self.keywords = set()
        self.statement_handlers = {}
        self.type_block_handlers = {}

    def register_statement(self, keyword, handler_func):
        """Rekisteröi avainsanan, joka aloittaa lausekkeen (esim. 'dim', 'sub')."""
        self.keywords.add(keyword.lower())
        self.statement_handlers[keyword.lower()] = handler_func

    def register_type_block_keyword(self, keyword, handler_func):
        """Rekisteröi avainsanan, joka voi esiintyä TYPE-lohkossa (esim. 'declare', 'static')."""
        self.keywords.add(keyword.lower())
        self.type_block_handlers[keyword.lower()] = handler_func

    def is_keyword(self, value):
        """Tarkista onko annettu arvo rekisteröity avainsana."""
        return value.lower() in self.keywords

class Tokenizer:
    KEYWORD_REGISTRY = None

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
                if ch in '(),:':
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
                    ttype = "KEYWORD" if self.KEYWORD_REGISTRY.is_keyword(value) else "IDENT"
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
    def __init__(self, name, type_name, visibility="public", is_static=False):
        super().__init__("Field")
        self.name = name
        self.type_name = type_name
        self.visibility = visibility
        self.is_static = is_static

class MethodNode(ASTNode):
    def __init__(self, name, params, return_type, visibility="public"):
        super().__init__("Method")
        self.name = name
        self.params = params
        self.return_type = return_type
        self.visibility = visibility

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
        self.static_fields = []

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
                if getattr(f, "visibility", "public").lower() != "public":
                    continue
                members.append({
                    "label": f.name,
                    "insertText": f.name,
                    "detail": f"(Member) {f.name} As {f.type_name}"
                })
            for m in ts.methods:
                if getattr(m, "visibility", "public").lower() != "public":
                    continue
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
    @staticmethod
    def create_default_registry():
        registry = KeywordRegistry()
        registry.register_statement("#include", Parser.parseInclude)
        registry.register_statement("type", Parser.parseType)
        registry.register_statement("dim", Parser.parseDim)
        registry.register_statement("as", None)  # <-- lisätty
        registry.register_type_block_keyword("declare", Parser.parseTypeMethod)
        registry.register_type_block_keyword("static", Parser.parseStaticField)
        registry.register_type_block_keyword("public", None)
        registry.register_type_block_keyword("private", None)
        return registry


    def __init__(self, tokens, symbol_table, base_path=""):
        self.tokens = tokens
        self.pos = 0
        self.symbol_table = symbol_table
        self.base_path = base_path
        self.registry = Tokenizer.KEYWORD_REGISTRY
        self.statement_handlers = self.registry.statement_handlers.copy()

    # === UTILITY FUNCTIONS ===
    def current(self):
        return self.tokens[self.pos]

    def peek(self, offset=1):
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return Token("EOF", "", self.current().line, self.current().column)

    def advance(self):
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return self.current()

    def match(self, type_, value=None):
        tok = self.current()
        if tok.type == type_ and (value is None or tok.value.lower() == value.lower()):
            self.advance()
            return True
        return False

    def expect(self, type_, value=None):
        tok = self.current()
        if tok.type == type_ and (value is None or tok.value.lower() == value.lower()):
            self.advance()
            return tok
        raise SyntaxError(f"Expected {type_} '{value}' at line {tok.line}, got {tok.type} '{tok.value}'")

    # === PARSER LOGIC ===
    def parseBlock(self):
        nodes = []
        while self.current().type != "EOF":
            node = self.parseStatement()
            if node:
                nodes.append(node)
        return nodes

    def parseStatement(self):
        tok = self.current()
        if tok.type == "KEYWORD":
            handler = self.statement_handlers.get(tok.value.lower())
            if handler:
                return handler(self)
        self.advance()
        return None

    def parseInclude(self):
        self.expect("KEYWORD", "#include")
        if self.match("KEYWORD", '"') or self.match("IDENT", '"'):
            path_tok = self.expect("IDENT")
            inc_name = path_tok.value
            self.expect("KEYWORD", '"')
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
        return None

    def parseVisibility(self):
        tok = self.current()
        if tok.type == "KEYWORD" and tok.value.lower() in ("public", "private"):
            vis = tok.value.lower()
            self.advance()
            if self.match("COMMA") or self.match("KEYWORD", ":"):
                pass
            return vis
        return None

    def parseType(self):
        self.expect("KEYWORD", "type")
        name_tok = self.expect("IDENT")
        fields = []
        methods = []
        current_visibility = "public"

        while True:
            tok = self.current()
            if tok.type == "KEYWORD" and tok.value.lower() == "end":
                break
            # käsittele public/private näkyvyydet
            if tok.type == "KEYWORD" and tok.value.lower() in ("public", "private"):
                current_visibility = tok.value.lower()
                self.advance()
                self.match("COMMA")
                self.match("KEYWORD", ":")
                continue
            # käsittele declare function/sub metodit
            if tok.type == "KEYWORD" and tok.value.lower() == "declare":
                method = self.parseTypeMethod(current_visibility)
                if method:
                    methods.append(method)
                continue
            # tavalliset kentät: IDENT as IDENT
            if tok.type == "IDENT":
                field = self.parseTypeField(current_visibility)
                if field:
                    fields.append(field)
                continue
            # jos mikään ei osu, ohita token
            self.advance()

        self.expect("KEYWORD", "end")
        self.expect("KEYWORD", "type")

        type_node = TypeNode(name_tok.value, fields, methods)
        type_symbol = TypeSymbol(type_node.name, type_node.fields, type_node.methods)
        for f in type_node.fields:
            if f.is_static:
                type_symbol.static_fields.append(f)
        self.symbol_table.addType(type_symbol)

        return type_node
    




    def _set_visibility(self, vis, current_vis):
        current_vis = vis
        self.advance()
        return None

    def parseTypeField(self, visibility="public"):
        # käsitellään public/private etukäteen
        tok = self.current()
        if tok.type == "KEYWORD" and tok.value.lower() in ("public", "private"):
            visibility = tok.value.lower()
            self.advance()
            self.match("COMMA")
            self.match("KEYWORD", ":")  # hyväksytään kaksoispiste
        # käsitellään static
        is_static = False
        tok = self.current()
        if tok.type == "KEYWORD" and tok.value.lower() == "static":
            is_static = True
            self.advance()
        # varsinainen kenttä
        name_tok = self.expect("IDENT")
        self.expect("KEYWORD", "as")
        type_tok = self.expect("IDENT")
        return FieldNode(name_tok.value, type_tok.value, visibility, is_static)



    def parseTypeMethod(self, visibility="public"):
        self.expect("KEYWORD", "declare")
        tok = self.current()
        if (tok.type == "KEYWORD" or tok.type == "IDENT") and tok.value.lower() in ("function", "sub"):
            kind = tok.value.lower()  # tallenna, onko function vai sub
            self.advance()
            name_tok = self.expect("IDENT")
            params = self.parseParameters()
            return_type = None
            if kind == "function":
                if self.match("KEYWORD", "as"):
                    return_type_tok = self.expect("IDENT")
                    return_type = return_type_tok.value
            return MethodNode(name_tok.value, params, return_type, visibility)
        else:
            self.advance()
            return None


    def parseParameters(self):
        params = []
        if self.match("KEYWORD", "("):
            while not self.match("KEYWORD", ")"):
                param_name = self.expect("IDENT").value
                param_type = None
                if self.match("KEYWORD", "as"):
                    param_type = self.expect("IDENT").value
                params.append((param_name, param_type))
                self.match("COMMA")
        return params

    def parseDim(self):
        self.expect("KEYWORD", "dim")
        names = []
        type_name = None
        while True:
            tok = self.current()
            if tok.type in ("IDENT", "KEYWORD"):
                names.append(tok.value)
                self.advance()
            else:
                break
            if not self.match("COMMA"):
                break
        if self.match("KEYWORD", "as"):
            type_name = self.expect("IDENT").value
            for n in names:
                self.symbol_table.addVariable(VariableSymbol(n, type_name))
        dim_node = DimNode(names, type_name)
        return dim_node

    def parseStaticField(self, visibility="public"):
        self.expect("KEYWORD", "static")
        name_tok = self.expect("IDENT")
        self.expect("KEYWORD", "as")
        type_tok = self.expect("IDENT")
        return FieldNode(name_tok.value, type_tok.value, visibility, is_static=True)

# === AI_INSERT_POINT:UTILITY_FUNCTIONS ===
# Alustetaan rekisteri nyt, kun Parser on täysin määritelty
Tokenizer.KEYWORD_REGISTRY = Parser.create_default_registry()
