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

    @staticmethod
    def create_default_registry():
        registry = KeywordRegistry()
        registry.register_statement("#include", Parser.parseInclude)
        registry.register_statement("type", Parser.parseType)
        
        registry.register_statement("as", None)  # <-- lisätty
        registry.register_type_block_keyword("declare", Parser.parseTypeMethod)
        registry.register_type_block_keyword("static", Parser.parseStaticField)
        registry.register_type_block_keyword("public", None)
        registry.register_type_block_keyword("private", None)

        # - lisäyskorvaus alkaa: Parser / create_default_registry / vaihe 21
        registry.register_statement("end", None)
        registry.register_statement("function", None)
        registry.register_statement("sub", None)
        registry.register_statement("shared", None)
        registry.register_statement("to", None)
        registry.register_statement("ptr", None)
        # - lisäyskorvaus loppuu

        return registry


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

        registry.keywords.add("#include")

        registry.register_statement("dim", Parser.parseDim)
        registry.register_statement("as", None)

        registry.register_type_block_keyword("declare", Parser.parseTypeMethod)
        registry.register_type_block_keyword("static", Parser.parseStaticField)
        registry.register_type_block_keyword("public", None)
        registry.register_type_block_keyword("private", None)

        return registry

    # Dataohjattu syntaksiperheiden määrittely
    grammar_table = {
        "include": {
            "patterns": [
                ["#include", "\"", "IDENT", "\""]
            ],
            "handler": "parseInclude"
        },
        "dim": {
            "patterns": [
                ["Dim", "IDENT", "As", "IDENT"],
                ["Dim", "IDENT", "As", "IDENT"],
                ["Dim", "IDENT", "IDENT"]
            ],
            "handler": "parseDim"
        },
        "var_decl": {
            "patterns": [
                ["IDENT"],
                ["IDENT", "ArraySpec"],
                ["IDENT", "Initializer"],
                ["IDENT", "ArraySpec", "Initializer"]
            ],
            "handler": "parseVarDecl"
        },
        "type_grammar": {
            "patterns": [
                ["IDENT"],
                ["IDENT", "*", "NUMBER"],
                ["IDENT", "Ptr"],
                ["IDENT", "Ptr", "Ptr"],
                ["Function", "(", "ParamList", ")", "As", "IDENT"]
            ],
            "handler": "parseTypeGrammar"
        },
        "expr": {
            "patterns": [
                ["NUMBER"],
                ["IDENT"],
                ["IDENT", "(", "ExprList", ")"],
                ["Expr", "+", "Expr"],
                ["Expr", "-", "Expr"],
                ["Expr", "*", "Expr"],
                ["Expr", "/", "Expr"]
            ],
            "handler": "parseExpr"
        },
        "exprlist": {
            "patterns": [
                ["Expr"],
                ["Expr", "COMMA", "ExprList"]
            ],
            "handler": "parseExprList"
        },
        "arrayspec": {
            "patterns": [
                ["(", "Expr", ")"],
                ["(", "Expr", "To", "Expr", ")"]
            ],
            "handler": "parseArraySpec"
        },
        "initializer": {
            "patterns": [
                ["=", "Expr"],
                ["=>", "Expr"]
            ],
            "handler": "parseInitializer"
        },
        "paramlist": {
            "patterns": [
                ["Param"],
                ["Param", "COMMA", "ParamList"]
            ],
            "handler": "parseParamList"
        },
        "type_syntax": {
            "patterns": [
                ["IDENT"],
                ["IDENT", "*", "NUMBER"],
                ["IDENT", "Ptr"],
                ["IDENT", "Ptr", "Ptr"]
            ],
            "handler": "parseTypeSyntax"
        },
        "type_field": {
            "patterns": [
                ["IDENT", "As", "IDENT"]
            ],
            "handler": "parseTypeField"
        },
        "type_static_field": {
            "patterns": [
                ["Static", "IDENT", "As", "IDENT"]
            ],
            "handler": "parseStaticField"
        },
        "type_visibility_field": {
            "patterns": [
                ["Public", ":", "IDENT", "As", "IDENT"],
                ["Private", ":", "IDENT", "As", "IDENT"]
            ],
            "handler": "parseTypeField"
        },
        "type_method": {
            "patterns": [
                ["Declare", "Function", "IDENT", "(", "ParamList", ")", "As", "IDENT"],
                ["Declare", "Sub", "IDENT", "(", "ParamList", ")"]
            ],
            "handler": "parseTypeMethod"
        }
    }


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

    def _match_pattern(self, pattern):
        """
        Yrittää matchata patternin nykyisestä token‑positiosta.
        Pattern on lista merkkijonoja, esim:
            ["Identifier", "As", "Type"]
        Palauttaa True/False.
        """
        for i, pat in enumerate(pattern):
            tok = self.peek(i)
            # Normalisoi tokenin "symbolinen nimi"
            tname = tok.type if tok.type != "KEYWORD" else tok.value.capitalize()

            if tname.lower() != pat.lower():
                return False
        return True

    def _dispatch_grammar(self):
        for key, entry in self.grammar_table.items():
            for pattern in entry["patterns"]:
                if self._match_pattern(pattern):
                    handler = getattr(self, entry["handler"], None)
                    if handler:
                        return handler()
        return None

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
        if tok.type == "KEYWORD" and tok.value.lower() == "type":
            return self.parseTypeBlock()
        if tok.type == "KEYWORD" and tok.value.lower() == "end":
            nxt = self.peek()
            if nxt.type == "KEYWORD" and nxt.value.lower() == "type":
                self.advance()
                self.advance()
                return None
        node = self._dispatch_grammar()
        if node is not None:
            return node
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
            tok = self.current()  # <-- tässä määritellään tok
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

#==================================
    def parseType(self):
        return self.parseTypeBlock()

    def parsePlainField(self, visibility="public"):
        """Käsittelee tavallisen kentän IDENT AS IDENT"""
        name_tok = self.expect("IDENT")
        self.expect("KEYWORD", "as")
        type_tok = self.expect("IDENT")
        return FieldNode(name_tok.value, type_tok.value, visibility)

#=================================
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
#=============================================

    def parseDim(self):
        """Pääfunktio DIM-lauseelle, tukee kaikkia FreeBASICin muotoja."""
        self.expect("KEYWORD", "dim")

        shared = False
        if self.match("KEYWORD", "shared"):
            shared = True

        variables = []
        type_name = None

        # Tarkista DIM AS Type -muoto
        if self.match("KEYWORD", "as"):
            type_name, variables = self.parseDimAsType()
        else:
            variables, type_name = self.parseDimNamesThenType()

        # Arrayt ja initializerit jokaiselle muuttujalle
        array_bounds_list = []
        initializer = None
        for idx, var in enumerate(variables):
            bounds, init = self.parseDimVarExtras()
            array_bounds_list.append(bounds)
            if idx == 0:  # FB sallii initializer vain ensimmäiselle muuttujalle
                initializer = init

            # Lisää symbolitauluun
            self.symbol_table.addVariable(VariableSymbol(var, type_name))

        node = DimNode(variables, type_name)
        node.array_bounds = array_bounds_list
        node.initializer = initializer
        node.shared = shared
        return node

    def parseDimAsType(self):
        """DIM AS TypeName var1, var2 ..."""
        type_name = self.expect("IDENT").value
        variables = []

        while True:
            var_tok = self.expect("IDENT")
            variables.append(var_tok.value)
            if not self.match("COMMA"):
                break

        return type_name, variables

    def parseDimNamesThenType(self):
        """DIM var1, var2 ... AS TypeName tai suffix-muodot"""
        variables = []
        type_name = None

        while True:
            tok = self.current()
            if tok.type != "IDENT":
                break
            var_name = tok.value

            # Suffix-tuki (%, $, #, !, &)
            suffix_map = {'$': 'String', '%': 'Integer', '#': 'Double', '!': 'Single', '&': 'LongInt'}
            if var_name[-1:] in suffix_map:
                type_name = suffix_map[var_name[-1:]]
                var_name = var_name[:-1]

            variables.append(var_name)
            self.advance()
            if not self.match("COMMA"):
                break

        # Jos rivillä on AS TypeName
        if self.match("KEYWORD", "as"):
            type_name = self.expect("IDENT").value

        return variables, type_name

    def parseDimVarExtras(self):
        """Käsittelee array bounds ja initializer jokaiselle muuttujalle."""
        bounds = []
        initializer = None

        # Array-spesifikaatio
        if self.match("KEYWORD", "("):
            while not self.match("KEYWORD", ")"):
                tok = self.current()
                if tok.type == "NUMBER":
                    bounds.append(int(tok.value))
                elif tok.type == "KEYWORD" and tok.value.lower() == "to":
                    bounds.append("to")
                elif tok.type == "IDENT":
                    bounds.append(tok.value)
                elif tok.type == "KEYWORD" and tok.value == "...":
                    bounds.append("...")
                self.advance()

        # Initializer
        if self.match("KEYWORD", "=") or self.match("KEYWORD", "=>"):
            init_tok = self.current()
            initializer = init_tok.value
            self.advance()

        return bounds, initializer

#================================================================
    def parseStaticField(self, visibility="public"):
        self.expect("KEYWORD", "static")
        name_tok = self.expect("IDENT")
        self.expect("KEYWORD", "as")
        type_tok = self.expect("IDENT")
        return FieldNode(name_tok.value, type_tok.value, visibility, is_static=True)

    # - lisäyskorvaus alkaa: Parser / parseVarDecl / vaihe 5
    def parseVarDecl(self):
        """Stub-var_decl handler (vaihe 5)."""
        tok = self.current()
        if tok.type == "IDENT":
            name = tok.value
            self.advance()
            return {"kind": "VarDecl", "name": name}
        return None
    # - lisäyskorvaus loppuu
    # - lisäyskorvaus alkaa: Parser / parseTypeGrammar / vaihe 7
    def parseTypeGrammar(self):
        """Stub-type_grammar handler (vaihe 7)."""
        tok = self.current()
        if tok.type == "IDENT":
            name = tok.value
            self.advance()
            return {"kind": "TypeGrammar", "name": name}
        return None
    # - lisäyskorvaus loppuu
    # - lisäyskorvaus alkaa: Parser / parseExpr / vaihe 9
    def parseExpr(self):
        """Stub-expr handler (vaihe 9)."""
        tok = self.current()
        if tok.type in ("NUMBER", "IDENT"):
            value = tok.value
            self.advance()
            return {"kind": "Expr", "value": value}
        return None
    # - lisäyskorvaus loppuu
    # - lisäyskorvaus alkaa: Parser / parseExprList / vaihe 11
    def parseExprList(self):
        """Stub-exprlist handler (vaihe 11)."""
        items = []
        expr = self.parseExpr()
        if expr:
            items.append(expr)
        while self.current().type == "COMMA":
            self.advance()
            expr = self.parseExpr()
            if expr:
                items.append(expr)
            else:
                break
        return {"kind": "ExprList", "items": items}
    # - lisäyskorvaus loppuu
    # - lisäyskorvaus alkaa: Parser / parseArraySpec / vaihe 13
    def parseArraySpec(self):
        """Stub-arrayspec handler (vaihe 13)."""
        items = []
        if self.match("KEYWORD", "("):
            # read until ')'
            while not self.match("KEYWORD", ")"):
                tok = self.current()
                items.append(tok.value)
                self.advance()
        return {"kind": "ArraySpec", "items": items}
    # - lisäyskorvaus loppuu
    # - lisäyskorvaus alkaa: Parser / parseInitializer / vaihe 15
    def parseInitializer(self):
        """Stub-initializer handler (vaihe 15)."""
        items = []
        tok = self.current()
        if tok.type == "KEYWORD" and tok.value in ("=", "=>"):
            op = tok.value
            self.advance()
            expr = self.parseExpr()
            return {"kind": "Initializer", "op": op, "expr": expr}
        return None
    # - lisäyskorvaus loppuu
    # - lisäyskorvaus alkaa: Parser / parseParamList / vaihe 17
    def parseParamList(self):
        """Stub-paramlist handler (vaihe 17)."""
        items = []
        tok = self.current()
        if tok.type == "IDENT":
            name = tok.value
            self.advance()
            items.append({"kind": "Param", "name": name})
        while self.current().type == "COMMA":
            self.advance()
            tok = self.current()
            if tok.type == "IDENT":
                name = tok.value
                self.advance()
                items.append({"kind": "Param", "name": name})
            else:
                break
        return {"kind": "ParamList", "items": items}
    # - lisäyskorvaus loppuu
    # - lisäyskorvaus alkaa: Parser / parseTypeSyntax / vaihe 19
    def parseTypeSyntax(self):
        """Stub-type_syntax handler (vaihe 19)."""
        tok = self.current()
        if tok.type == "IDENT":
            name = tok.value
            self.advance()
            return {"kind": "TypeSyntax", "name": name}
        return None
    # - lisäyskorvaus loppuu



# === AI_INSERT_POINT:UTILITY_FUNCTIONS ===
# Alustetaan rekisteri nyt, kun Parser on täysin määritelty

    def parseExpr_at(self, pos):
        """
        Kokeile parsia Expr alkaen annetusta pos-indeksistä.
        Ei muuta self.pos-arvoa.
        Palauttaa (node, new_pos) tai (None, pos).
        """
        tokens = self.tokens
        length = len(tokens)

        # Jos pos on ulkona, ei matchia
        if pos >= length:
            return None, pos

        tok = tokens[pos]

        # 1) NUMBER → Expr
        if tok.type == "NUMBER":
            return {"kind": "Expr", "value": tok.value}, pos + 1

        # 2) IDENT → Expr
        if tok.type == "IDENT":
            return {"kind": "Expr", "value": tok.value}, pos + 1

        # 3) IDENT "(" ... ")"  (kokeiluversio funktiokutsulle)
        if tok.type == "IDENT":
            if pos + 1 < length and tokens[pos + 1].type == "(":
                i = pos + 2
                depth = 1
                while i < length:
                    if tokens[i].type == "(":
                        depth += 1
                    elif tokens[i].type == ")":
                        depth -= 1
                        if depth == 0:
                            return {"kind": "ExprCall", "name": tok.value}, i + 1
                    i += 1

        # Ei matchia
        return None, pos
Tokenizer.KEYWORD_REGISTRY = Parser.create_default_registry()

    def parseTypeBlock(self):
        self.expect("KEYWORD", "Type")
        type_name_tok = self.expect("IDENT")
        tnode = TypeNode(name=type_name_tok.value, fields=[], methods=[])
        self.symbol_table.addType(TypeSymbol(tnode.name, [], []))
        current_visibility = "public"
        while True:
            tok = self.current()
            if tok.type == "KEYWORD":
                val = tok.value.lower()
                if val == "end" and self.peek().type == "KEYWORD" and self.peek().value.lower() == "type":
                    self.advance()
                    self.advance()
                    break
                if val in ("public", "private"):
                    current_visibility = val
                    self.advance()
                    if self.current().type == ":" or (self.current().type == "KEYWORD" and self.current().value == ":"):
                        self.advance()
                    continue
                if val == "static":
                    fnode = self.parseStaticField(current_visibility)
                    tnode.fields.append(fnode)
                    continue
                if val == "dim":
                    dim_node = self.parseDim()
                    for n in dim_node.names:
                        fnode = FieldNode(n, dim_node.type_name, current_visibility)
                        tnode.fields.append(fnode)
                    continue
                if val == "declare":
                    mnode = self.parseTypeMethod(current_visibility)
                    if mnode:
                        tnode.methods.append(mnode)
                    continue
            if tok.type == "IDENT":
                fnode = self.parsePlainField(current_visibility)
                tnode.fields.append(fnode)
                continue
            self.advance()
        return tnode
