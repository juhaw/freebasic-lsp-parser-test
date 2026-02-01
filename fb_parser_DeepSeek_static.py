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
    # Alustetaan myöhemmin, kun Parser-luokka on määritelty
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
                    # Käytetään nyt rekisteriä avainsanojen tarkistamiseen
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
    # === AI_INSERT_POINT:PARSER_CLASS_HEADER ===
    @staticmethod
    def create_default_registry():
        """Luo oletusrekisterin kaikilla nykyisillä käskyillä."""
        registry = KeywordRegistry()
        
        # Rekisteröi kaikki nykyiset lausekkeen aloittavat avainsanat
        registry.register_statement("#include", Parser.parseInclude)
        registry.register_statement("type", Parser.parseType)
        registry.register_statement("dim", Parser.parseDim)
        # LISÄÄ UUSIA LAUSEKKEIDEN KÄSITTELIJÖITÄ TÄHÄN
        # esim: registry.register_statement("sub", Parser.parseSub)
        #       registry.register_statement("function", Parser.parseFunction)
        
        # Rekisteröi TYPE-lohkon sisäiset avainsanat
        registry.register_type_block_keyword("declare", Parser.parseTypeMethod)
        registry.register_type_block_keyword("static", Parser.parseStaticField)
        # public ja private käsitellään erikseen TYPE-lohkossa
        registry.register_type_block_keyword("public", None)
        registry.register_type_block_keyword("private", None)
        # LISÄÄ UUSIA TYPE-LOHKON KÄSITTELIJÖITÄ TÄHÄN
        
        return registry

    def __init__(self, tokens, symbol_table, base_path=""):
        self.tokens = tokens
        self.pos = 0
        self.symbol_table = symbol_table
        self.base_path = base_path
        
        # Käytetään keskitettyä rekisteriä
        self.registry = Tokenizer.KEYWORD_REGISTRY
        
        # Lausekkeen käsittelijät haetaan rekisteristä
        self.statement_handlers = self.registry.statement_handlers.copy()

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
            handler = self.statement_handlers.get(tok.value.lower())
            if handler:
                # Kutsu käsittelijää ilman ylimääräisiä parametreja
                return handler(self)
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
        return None

    def parseVisibility(self):
        tok = self.current()
        if tok.type == "KEYWORD" and tok.value.lower() in ("public", "private"):
            vis = tok.value.lower()
            self.advance()
            if self.current().value == ":":
                self.advance()
            return vis
        return None

    def parseType(self):
        # Odotetaan TYPE-avainsanaa
        self.expect_keyword("type")
        name_tok = self.expect_ident()

        fields = []
        methods = []
        current_visibility = "public"

        # === AI_INSERT_POINT:TYPE_BODY ===
        # Helper: päivittää näkyvyyden
        def set_visibility(vis):
            nonlocal current_visibility
            current_visibility = vis
            return None

        # TYPE-body sanakirja - nyt käytetään rekisteriä
        type_keyword_handlers = {
            "public": lambda: set_visibility("public"),
            "private": lambda: set_visibility("private"),
        }
        
        # Lisää rekisteröidyt TYPE-lohkon käsittelijät
        for keyword, handler in self.registry.type_block_handlers.items():
            if handler is not None:  # Ohitetaan public/private jotka käsitellään erikseen
                type_keyword_handlers[keyword] = lambda h=handler: h(self, current_visibility)

        # TYPE-body silmukka
        while True:
            tok = self.current()

            # Lopetusehto: END TYPE
            if tok.type == "KEYWORD" and tok.value.lower() == "end":
                break

            handled = False
            v = tok.value.lower() if tok.type == "KEYWORD" else None

            # 1️⃣ Käsitellään avainsanat sanakirjalla
            if tok.type == "KEYWORD" and v in type_keyword_handlers:
                node = type_keyword_handlers[v]()
                # Varmista aina eteneminen, jos handler ei siirrä tokenia
                if self.current() == tok:
                    self.advance()

                # Lisää AST:ään
                if node:
                    if isinstance(node, MethodNode):
                        methods.append(node)
                    elif isinstance(node, FieldNode):
                        fields.append(node)
                handled = True

            # 2️⃣ IDENT → kenttä
            elif tok.type == "IDENT":
                field = self.parseTypeField(current_visibility)
                if field:
                    fields.append(field)
                # parseTypeField etenee tokenissa itsessään
                handled = True

            # 3️⃣ Jos token ei ollut käsitelty, siirrytään seuraavaan
            if not handled:
                self.advance()

        # Odotetaan END TYPE
        self.expect_keyword("end")
        self.expect_keyword("type")

        # Luodaan AST-solmu
        type_node = TypeNode(name_tok.value, fields, methods)

        # Symbolitaulu
        type_symbol = TypeSymbol(type_node.name, type_node.fields, type_node.methods)
        for f in type_node.fields:
            if getattr(f, "is_static", False):
                type_symbol.static_fields.append(f)
        self.symbol_table.addType(type_symbol)

        return type_node

#======================================

    def parseTypeField(self, visibility="public"):
        name_tok = self.expect_ident()
        if not self.match_keyword("as"):
            return None
        type_tok = self.expect_ident()
        return FieldNode(name_tok.value, type_tok.value, visibility)

# Esimerkki parseTypeMethod
    def parseTypeMethod(self, visibility="public"):
        # Tämä on nyt TYPE-lohkon sisäinen käsittelijä
        self.expect_keyword("declare")
        tok = self.current()
        if tok.type == "KEYWORD" and tok.value.lower() == "function":
            self.advance()
            name_tok = self.expect_ident()
            # Käsittele parametrit ja paluuarvo
            # TÄYTÄ TÄHÄN PARAMETRIEN JA PALUUARVON KÄSITTELY
            # esim: self.parseParameters() ja self.parseReturnType()
            return MethodNode(name_tok.value, [], None, visibility)
        elif tok.type == "KEYWORD" and tok.value.lower() == "sub":
            self.advance()
            name_tok = self.expect_ident()
            # Käsittele parametrit
            # TÄYTÄ TÄHÄN PARAMETRIEN KÄSITTELY
            return MethodNode(name_tok.value, [], None, visibility)
        else:
            # Jos ei function/sub → siirry seuraavaan
            self.advance()
            return None

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

    def parseStaticField(self, visibility="public"):
        # Tämä on nyt TYPE-lohkon sisäinen käsittelijä
        self.expect_keyword("static")
        name_tok = self.expect_ident()
        self.expect_keyword("as")
        type_tok = self.expect_ident()  # tyyppi
        # HUOM: expect_ident() jo siirtyy eteenpäin, joten self.advance() ei tarvita
        return FieldNode(name_tok.value, type_tok.value, visibility, is_static=True)

# === AI_INSERT_POINT:UTILITY_FUNCTIONS ===
# Alustetaan rekisteri vasta nyt, kun Parser-luokka on täysin määritelty
Tokenizer.KEYWORD_REGISTRY = Parser.create_default_registry()