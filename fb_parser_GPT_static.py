#```
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
    @staticmethod
    @staticmethod
    def create_default_registry():
        registry = KeywordRegistry()
        registry.register_statement("#include", Parser.parseInclude)
        registry.register_statement("type", Parser.parseTypeBlock)
        registry.register_statement("dim", Parser.parseDim)
        registry.register_statement("function", Parser.parseMethodImplementation)
        registry.register_statement("sub", Parser.parseMethodImplementation)
        registry.register_statement("declare", Parser.parseGlobalDeclare)
        registry.register_statement("constructor", Parser.parseMethodImplementation)
        registry.register_statement("destructor", Parser.parseMethodImplementation)
        registry.register_statement("as", None)
        registry.register_statement("end", None)
        registry.register_statement("shared", None)
        registry.register_statement("to", None)
        registry.register_statement("ptr", None)

        registry.register_type_block_keyword("declare", Parser._handle_type_declare)
        registry.register_type_block_keyword("static", Parser._handle_type_static)
        registry.register_type_block_keyword("dim", Parser._handle_type_dim)
        registry.register_type_block_keyword("property", Parser._handle_type_property)
        registry.register_type_block_keyword("constructor", Parser.handleConstructorDestructor)
        registry.register_type_block_keyword("destructor", Parser.handleConstructorDestructor)
        registry.register_type_block_keyword("public", None)
        registry.register_type_block_keyword("private", None)

        return registry

    def is_keyword(self, value):
        """Tarkista onko annettu arvo rekisteröity avainsana."""
        return value.lower() in self.keywords

    def get_type_block_handler(self, keyword):
        return self.type_block_handlers.get(keyword.lower())

class Tokenizer:
    def __init__(self, source, filename=""):
        self.source = source
        self.filename = filename
        self.tokens = []
        self.pos = 0
        self.line = 1
        self.col = 1
        self.current_char = source[0] if source else None

    def advance(self):
        """Siirtyy seuraavaan merkkiin ja päivittää rivi/sarake-tiedot."""
        self.pos += 1
        if self.pos < len(self.source):
            self.current_char = self.source[self.pos]
            self.col += 1
        else:
            self.current_char = None

    def peek(self):
        """Katsoo seuraavaa merkkiä liikuttamatta kursoria."""
        peek_pos = self.pos + 1
        if peek_pos < len(self.source):
            return self.source[peek_pos]
        return None

    def _tokenize(self):
        while self.current_char is not None:
            char = self.current_char

            if char.isspace():
                if char == '\n':
                    self.line += 1
                    self.col = 1
                self.advance()
                continue

            if char == "'":
                while self.current_char is not None and self.current_char != '\n':
                    self.advance()
                continue

            if char == '"':
                start_col = self.col
                val = ""
                self.advance()
                while self.current_char is not None and self.current_char != '"':
                    val += self.current_char
                    self.advance()
                if self.current_char == '"': self.advance()
                self.tokens.append(Token("STRING", val, self.line, start_col))
                continue

            if char.isdigit():
                start_col = self.col
                num = ""
                has_dec = False
                while self.current_char is not None:
                    if self.current_char == '.' and not has_dec:
                        nxt = self.peek()
                        if nxt and nxt.isdigit():
                            has_dec = True
                            num += self.current_char
                        else: break
                    elif self.current_char.isdigit():
                        num += self.current_char
                    else: break
                    self.advance()
                self.tokens.append(Token("NUMBER", num, self.line, start_col))
                continue

            if char.isalpha() or char == '_' or char == '#':
                start_col = self.col
                ident = ""
                while self.current_char is not None and (self.current_char.isalnum() or self.current_char == '_'):
                    ident += self.current_char
                    self.advance()

                if self.current_char is not None and self.current_char in "$%&!#":
                    ident += self.current_char
                    self.advance()

                if Tokenizer.KEYWORD_REGISTRY and Tokenizer.KEYWORD_REGISTRY.is_keyword(ident):
                    self.tokens.append(Token("KEYWORD", ident, self.line, start_col))
                else:
                    self.tokens.append(Token("IDENT", ident, self.line, start_col))
                continue

            if char == ',':
                self.tokens.append(Token("COMMA", ",", self.line, self.col))
                self.advance()
            elif char == '.':
                self.tokens.append(Token("DOT", ".", self.line, self.col))
                self.advance()
            elif char == ':':
                self.tokens.append(Token("COLON", ":", self.line, self.col))
                self.advance()
            elif char == '(':
                self.tokens.append(Token("LPAREN", "(", self.line, self.col))
                self.advance()
            elif char == ')':
                self.tokens.append(Token("RPAREN", ")", self.line, self.col))
                self.advance()
            elif char == '=':
                self.tokens.append(Token("KEYWORD", "=", self.line, self.col))
                self.advance()
            else:
                self.advance()

        self.tokens.append(Token("EOF", "", self.line, self.col))
        return self.tokens

    def get_tokens(self):
        return self.tokens

    KEYWORD_REGISTRY = None

class ASTNode:
    def __init__(self, kind):
        self.kind = kind

class TypeNode(ASTNode):
    def __init__(self, name, fields, methods):
        super().__init__("Type")
        self.name = name
        self.fields = fields
        self.methods = methods

    def add_method(self, name, return_type, params, visibility="public"):
        new_method = MethodNode(name, params, return_type, visibility)
        self.methods.append(new_method)

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

class AssignmentNode(ASTNode):
    def __init__(self, target, value):
        super().__init__("Assignment")
        self.target = target
        self.value = value

    def __repr__(self):
        return f"Assignment({self.target} = {self.value})"

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
                # Varmistetaan nimen haku MethodNode-oliolta
                m_name = getattr(m, 'name', 'Unknown')
                members.append({
                    "label": m_name,
                    "insertText": f"{m_name}($1)",
                    "detail": f"(Method) {m_name}"
                })
            result[ts.name] = members
        return result

    def var_to_type_dict(self):
        result = {}
        for name, vs in self.variables.items():
            result[vs.name] = vs.type
        return result

class Parser:
    # Dataohjattu syntaksiperheiden määrittely
    grammar_table = {
        "include": {
            "patterns": [["#include", "STRING"]],
            "handler": "parseInclude"
        },
        "dim": {
            "patterns": [["Dim"]],
            "handler": "parseDim"
        },
        "type": {
            "patterns": [["Type"]],
            "handler": "parseTypeBlock"
        },
        "var_decl": {
            "patterns": [["IDENT", "As", "IDENT"]],
            "handler": "parseVarDecl"
        }
    }

    def __init__(self, tokens, symbol_table=None, base_path=""):
        self.tokens = tokens
        self.pos = 0
        self.symbol_table = symbol_table if symbol_table else SymbolTable()
        self.base_path = base_path
        self.current_type = None
        self.registry = KeywordRegistry.create_default_registry()
        # Basic fields (no keyword) handled by default in parseTypeBlock

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
        for i, pat in enumerate(pattern):
            tok = self.peek(i)
            tname = tok.type if tok.type != "KEYWORD" else tok.value.capitalize()
            if tname.lower() != pat.lower():
                return False
        return True

    def _dispatch_grammar(self):
        for key, entry in self.grammar_table.items():
            for pattern in entry["patterns"]:
                if self._match_pattern(pattern):
                    handler = getattr(self, entry["handler"], None)
                    if handler: return handler()
        return None

    def parseBlock(self):
        nodes = []
        while self.current().type != "EOF":
            node = self.parseStatement()
            if node: nodes.append(node)
        return nodes

    def parseStatement(self):
        tok = self.current()

        # 1. Tarkistetaan rekisteröidyt avainsanat (dim, type, function, sub jne.)
        if tok.type == "KEYWORD":
            handler = self.registry.statement_handlers.get(tok.value.lower())
            if handler:
                return handler(self)

        # 2. Tarkistetaan sijoituslauseet (alkavat tunnisteella)
        if tok.type == "IDENT":
            node = self.parseAssignment()
            if node: return node

            # Jos ei sijoitus, ohitetaan rivi (esim. print tai muu kutsu)
            line = tok.line
            while self.current().type != "EOF" and self.current().line == line:
                self.advance()
            return None

        # 3. Tarkistetaan dataohjattu grammar_table muille rakenteille
        node = self._dispatch_grammar()
        if node is not None: return node

        self.advance()
        return None

    def parseInclude(self):
        self.expect("KEYWORD", "#include")
        tok = self.current()
        if tok.type == "STRING":
            inc_name = tok.value
            self.advance()
            full_path = os.path.join(self.base_path, inc_name)
            if os.path.exists(full_path):
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    code = f.read()
                tokenizer = tokenize_source(code, full_path)
                sub_parser = Parser(tokenizer.get_tokens(), self.symbol_table, os.path.dirname(full_path))
                sub_parser.parseBlock()
        else:
            line = tok.line
            while self.current().type != "EOF" and self.current().line == line:
                self.advance()
        return None

    def _handle_type_declare(self, visibility, tnode):
        self.consume()  # 'declare'

        token = self.current()
        if token.type == "KEYWORD" and token.value.lower() in ("constructor", "destructor"):
            return self.handleConstructorDestructor(visibility, tnode)

        # Tavallinen metodi (Function/Sub)
        kind = self.consume().value  # 'function' tai 'sub'
        name_tok = self.expect("IDENT")
        name = name_tok.value

        params = []
        if self.match("LPAREN", "("):
            while self.current().type != "RPAREN" and self.current().type != "EOF":
                if self.current().value.lower() in ("byval", "byref"):
                    self.advance()
                p_name = self.expect("IDENT").value
                p_type = "Any"
                if self.match("KEYWORD", "as"):
                    p_type = self.expect("IDENT").value
                params.append((p_name, p_type))
                if self.current().type == "COMMA":
                    self.advance()
            self.expect("RPAREN")

        ret_type = "Void"
        if kind.lower() == "function" and self.match("KEYWORD", "as"):
            ret_type = self.expect("IDENT").value

        new_method = MethodNode(name, params, ret_type, visibility)
        tnode.methods.append(new_method)
        if self.current_type:
            self.current_type.methods.append(new_method)

        return True, visibility

    def _handle_type_static(self, visibility, tnode):
        fnode = self.parseStaticField(visibility)
        if fnode:
            tnode.fields.append(fnode)
            # Päivitetään symbolitaulun TypeSymbol
            ts = self.symbol_table.getType(tnode.name)
            if ts:
                ts.fields.append(fnode)
                if fnode.is_static:
                    ts.static_fields.append(fnode)
        return True, visibility

    def _handle_type_dim(self, visibility, tnode):
        dim_node = self.parseDim()
        # Käydään läpi kaikki dim-lauseessa määritellyt nimet
        for i, n in enumerate(dim_node.names):
            # Haetaan kunkin muuttujan yksilöllinen tyyppi vars_meta-listasta
            # (tämä tukee esim. 'dim a as integer, b as string' -tyylisiä rakenteita)
            t_name = dim_node.vars_meta[i][1] if hasattr(dim_node, 'vars_meta') else dim_node.type_name
            fnode = FieldNode(n, t_name, visibility)
            tnode.fields.append(fnode)

            # Päivitetään myös symbolitaulussa oleva tyyppi-instanssi
            ts = self.symbol_table.getType(tnode.name)
            if ts:
                ts.fields.append(fnode)
        return True, visibility

    def _dispatch_type_block_line(self, current_visibility, tnode):
        tok = self.current()
        if tok.type == "KEYWORD" and tok.value.lower() in ("public", "private"):
            vis = tok.value.lower()
            self.advance()
            if self.current().type in ("COLON", "KEYWORD") and self.current().value == ":":
                self.advance()
            return True, vis
        if tok.type == "KEYWORD":
            handler = self.registry.get_type_block_handler(tok.value)
            if handler:
                res = handler(self, current_visibility, tnode)
                return res if isinstance(res, tuple) else (True, current_visibility)
        if tok.type == "IDENT" and self.peek().value.lower() == "as":
            fnode = self.parsePlainField(current_visibility)
            tnode.fields.append(fnode)
            ts = self.symbol_table.getType(tnode.name)
            if ts: ts.fields.append(fnode)
            return True, current_visibility
        return False, current_visibility

    def parseTypeBlock(self):
        self.expect("KEYWORD", "Type")
        name_tok = self.expect("IDENT")
        type_name = name_tok.value

        tnode = TypeNode(name=type_name, fields=[], methods=[])
        ts = TypeSymbol(type_name, [], [])
        self.symbol_table.addType(ts)

        self.current_type = ts
        current_visibility = "public"

        while self.current().type != "EOF":
            tok = self.current()
            if tok.value.lower() == "end" and self.peek().value.lower() == "type":
                self.advance() # end
                self.advance() # type
                break

            handled, current_visibility = self._dispatch_type_block_line(current_visibility, tnode)
            if not handled:
                self.advance()

        self.current_type = None
        return tnode

    def parsePlainField(self, visibility="public"):
        name = self.expect("IDENT").value
        self.expect("KEYWORD", "as")
        type_name = self.expect("IDENT").value
        # Tuki PTR-avainsanalle (esim. As Integer Ptr)
        if self.current().value.lower() == "ptr":
            type_name += " Ptr"
            self.advance()
        return FieldNode(name, type_name, visibility)

    def parseTypeMethod(self, visibility="public"):
        self.expect("KEYWORD", "declare")
        kind = self.current().value.lower()
        self.advance()
        name = self.expect("IDENT").value
        params = self.parseParameters()
        ret_type = self.expect("IDENT").value if kind == "function" and self.match("KEYWORD", "as") else None
        return MethodNode(name, params, ret_type, visibility)

    def parseParameters(self):
        params = []
        if self.match("KEYWORD", "("):
            while not self.match("KEYWORD", ")"):
                p_name = self.expect("IDENT").value
                p_type = self.expect("IDENT").value if self.match("KEYWORD", "as") else None
                params.append((p_name, p_type))
                self.match("COMMA")
        return params

    def parseDim(self):
        self.expect("KEYWORD", "dim")
        shared = self.match("KEYWORD", "shared")

        vars_info = []

        while True:
            name_tok = self.expect("IDENT")
            name = name_tok.value

            # Taulukon koon luku (esim. arr(10, 1 To 5))
            bounds = []
            if self.match("LPAREN"):
                while True:
                    part = []
                    while self.current().type not in ("RPAREN", "COMMA", "EOF"):
                        part.append(self.current().value)
                        self.advance()
                    bounds.append(" ".join(part))
                    if not self.match("COMMA"):
                        break
                self.expect("RPAREN")

            var_type = "Any"
            if self.match("KEYWORD", "as"):
                type_tok = self.expect("IDENT")
                var_type = type_tok.value
                if self.current().value.lower() == "ptr":
                    var_type += " Ptr"
                    self.advance()
            else:
                suffixes = {'$': 'String', '%': 'Integer', '#': 'Double', '!': 'Single', '&': 'LongInt'}
                var_type = suffixes.get(name[-1:], "Any")

            # Initializerin käsittely: syö kaiken kuten = Kangaroo(1) tai = 10
            initializer = None
            if self.current().value in ("=", "=>"):
                self.advance()
                init_parts = []
                start_line = name_tok.line
                # Luetaan kunnes rivi vaihtuu, tulee pilkku tai kaksoispiste
                while (self.current().type != "EOF" and 
                       self.current().line == start_line and 
                       self.current().value not in (",", ":")):
                    init_parts.append(self.current().value)
                    self.advance()
                initializer = " ".join(init_parts)

            vars_info.append((name, var_type, bounds, initializer))
            self.symbol_table.addVariable(VariableSymbol(name, var_type))

            if not self.match("COMMA"):
                break

        # Palautetaan DimNode, jotta testiohjelmasi tulostus "Parsed node: DimNode" toimii
        node = DimNode([v[0] for v in vars_info], vars_info[0][1])
        node.shared = shared
        node.vars_meta = vars_info 
        return node


    def parseStaticField(self, visibility="public"):
        self.expect("KEYWORD", "static")
        name_tok = self.expect("IDENT")
        name = name_tok.value
        type_name = "Any"
        if self.match("KEYWORD", "as"):
            type_tok = self.expect("IDENT")
            type_name = type_tok.value
            # Tuki pointterityypeille myös staattisissa kentissä
            if self.current().value.lower() == "ptr":
                type_name += " Ptr"
                self.advance()
        return FieldNode(name, type_name, visibility, is_static=True)

    def parseVarDecl(self):
        tok = self.current()
        if tok.type == "IDENT":
            name = tok.value
            self.advance()
            return {"kind": "VarDecl", "name": name}
        return None

    def parseExpr(self):
        tok = self.current()
        if tok.type in ("NUMBER", "IDENT"):
            val = tok.value
            self.advance()
            return {"kind": "Expr", "value": val}
        return None
    
    def parseAssignment(self):
        found_eq = False
        idx = self.pos
        start_line = self.tokens[idx].line

        # Etsitään onko rivillä '=' ennen seuraavaa lausetta (COLON tai rivinvaihto)
        while idx < len(self.tokens) and self.tokens[idx].line == start_line:
            if self.tokens[idx].type == "COLON":
                break
            if self.tokens[idx].type == "KEYWORD" and self.tokens[idx].value == "=":
                found_eq = True
                break
            idx += 1

        if not found_eq:
            return None

        target_parts = []
        # Luetaan kaikki ennen yhtäsuuruusmerkkiä (identit, pisteet, sulut)
        while self.current().type != "EOF" and not (self.current().type == "KEYWORD" and self.current().value == "="):
            target_parts.append(self.current().value)
            self.advance()

        target_str = "".join(target_parts).strip()
        self.match("KEYWORD", "=")

        value_tokens = []
        # Luetaan arvo seuraavaan komentoon tai rivin loppuun asti
        while self.current().type != "EOF" and self.current().line == start_line and self.current().value != ":":
            value_tokens.append(self.current().value)
            self.advance()

        value_str = " ".join(value_tokens).strip()

        if self.current().value == ":":
            self.advance()

        return AssignmentNode(target_str, value_str)
    def consume(self):
        tok = self.current()
        self.advance()
        return tok
    def parseMethodImplementation(self):
        token = self.advance()
        # method_type on esim. 'sub', 'function', 'constructor' tai 'destructor'
        method_type = token.value.lower()

        full_name = ""
        # Kerätään nimi, jos se seuraa avainsanaa (esim. 'Kangaroo.jump_set')
        while self.current().type in ("IDENT", "DOT"):
            full_name += self.current().value
            self.advance()

        # Jos nimeä ei löytynyt (esim. pelkkä 'Constructor'), käytetään tyyppiä nimenä
        # TÄSSÄ KOHTAA 'Kangaroo' voi tulla nimeksi jos 'Constructor' on jo syöty
        if not full_name:
            full_name = method_type

        # Ohitetaan parametrit ja paluutyypit, ne eivät vaikuta tähän ongelmaan
        params = []
        if self.match("LPAREN"):
            while self.current().type != "RPAREN" and self.current().type != "EOF":
                p_name = self.expect("IDENT").value
                self.expect("KEYWORD", "as")
                p_type = self.expect("IDENT").value
                params.append((p_name, p_type))
                if not self.match("COMMA"):
                    break
            self.expect("RPAREN")

        return_type = "Void"
        if self.match("KEYWORD", "as"):
            return_type = self.expect("IDENT").value

        # --- RATKAISU ---
        # 1. Jos nimessä on piste (Kangaroo.jump_set) -> se on luokan metodi.
        # 2. Jos method_type on constructor/destructor -> se on luokan metodi.
        # 3. Jos full_name on 'Kangaroo' ja meillä on tyyppi sen nimisenä -> se on luokan metodi.

        is_class_member = (
            "." in full_name or 
            method_type in ("constructor", "destructor") or 
            full_name.lower() in ("kangaroo", "constructor", "destructor")
        )

        if not is_class_member:
            self.symbol_table.addVariable(VariableSymbol(full_name, f"{method_type.capitalize()} returning {return_type}"))

        # Skipataan rungon sisältö 'end' -sanaan asti
        while self.current().type != "EOF":
            if self.match("KEYWORD", "end"):
                self.advance() # Ohitetaan 'sub'/'function' tms.
                break
            self.advance()

        return MethodNode(full_name, return_type, params)
    def _handle_type_property(self, visibility, tnode):
        # Ohitetaan 'property'
        self.advance()

        # Ominaisuuden nimi
        name_tok = self.expect("IDENT")
        prop_name = name_tok.value

        # Parametrit (Propertylla voi olla indeksejä, esim. Item(index As Integer))
        params = []
        if self.current().type == "LPAREN":
            self.advance()
            while self.current().type != "RPAREN" and self.current().type != "EOF":
                # Ohitetaan FreeBasicin ByVal/ByRef avainsanat
                if self.current().value.lower() in ("byval", "byref"):
                    self.advance()

                p_name_tok = self.expect("IDENT")
                p_name = p_name_tok.value
                p_type = "Any"
                if self.current().value.lower() == "as":
                    self.advance()
                    p_type = self.current().value
                    self.advance()
                params.append((p_name, p_type))
                if self.current().type == "COMMA":
                    self.advance()
            self.expect("RPAREN")

        # Paluutyyppi (Propertylla on aina tyyppi)
        ret_type = "Any"
        if self.current().value.lower() == "as":
            self.advance()
            ret_type = self.current().value
            self.advance()

        # Lisätään tieto AST-solmuun ja symbolitauluun
        # Käytetään MethodNodea, koska Property käyttäytyy kutsuessa samoin
        new_prop = MethodNode(prop_name, params, ret_type, visibility)
        tnode.methods.append(new_prop)
        if self.current_type:
            self.current_type.methods.append(new_prop)

        return True, visibility
    def parseGlobalDeclare(self):
        self.expect("KEYWORD", "declare")
        kind = self.current().value.lower() # sub tai function
        self.advance()

        name = self.expect("IDENT").value
        # Tässä voisi parsia parametrit samoin kuin yllä, 
        # mutta lisätään se nyt ainakin symbolitauluun
        self.symbol_table.addVariable(VariableSymbol(name, f"Declared {kind}"))

        # Ohitetaan loppurivi
        line = self.current().line
        while self.current().line == line and self.current().type != "EOF":
            self.advance()
        return None
    def handleConstructorDestructor(self, visibility, tnode):
        kind_tok = self.consume()  # 'constructor' tai 'destructor'
        method_name = kind_tok.value
        params = []

        # Jos perässä on IDENT, se on metodin nimi (harvinaisempaa konstruktoreille, mutta mahdollista)
        if self.current().type == "IDENT":
            method_name = self.consume().value

        if self.match("LPAREN", "("):
            while self.current().type != "RPAREN" and self.current().type != "EOF":
                if self.current().value.lower() in ("byval", "byref"): 
                    self.advance()

                if self.current().type == "IDENT":
                    p_name = self.consume().value
                    p_type = "Any"
                    if self.match("KEYWORD", "as"):
                        if self.current().type == "IDENT":
                            p_type = self.consume().value
                    params.append((p_name, p_type))

                if self.current().type == "COMMA":
                    self.advance()
                elif self.current().type != "RPAREN":
                    self.advance()

            self.expect("RPAREN")

        new_method = MethodNode(method_name, params, "None", visibility)
        tnode.methods.append(new_method)
        if self.current_type:
            self.current_type.methods.append(new_method)

        return True, visibility
    def _handle_dim(self, is_shared=False):
        self.consume()  # 'dim' tai 'redim'
        if self.current().value.lower() == "shared":
            self.advance()
            is_shared = True

        while True:
            name_tok = self.expect("IDENT")
            name = name_tok.value

            # Ohitetaan taulukkomääritykset (esim. arr(10))
            if self.match("LPAREN", "("):
                while self.current().type != "RPAREN" and self.current().type != "EOF":
                    self.advance()
                self.expect("RPAREN")

            var_type = "Any"
            if self.match("KEYWORD", "as"):
                # Huomioidaan myös mahdolliset pointterit: As Integer Ptr
                type_tok = self.expect("IDENT")
                var_type = type_tok.value
                if self.current().value.lower() == "ptr":
                    var_type += " Ptr"
                    self.advance()

            # Lisätään muuttuja symbolitauluun
            self.symbol_table.addVariable(VariableSymbol(name, var_type))

            # TÄRKEÄÄ: Jos perässä on '=', kulutetaan loppurivi jotta se ei sotke seuraavia hakuja
            if self.match("KEYWORD", "="):
                start_line = name_tok.line
                while self.current().type != "EOF" and self.current().line == start_line and self.current().value != ":":
                    self.advance()

            if not self.match("COMMA", ","):
                break

        return None


Tokenizer.KEYWORD_REGISTRY = KeywordRegistry.create_default_registry()


def tokenize_source(source, filename=""):
    if Tokenizer.KEYWORD_REGISTRY is None:
        Tokenizer.KEYWORD_REGISTRY = KeywordRegistry.create_default_registry()
    t = Tokenizer(source, filename)
    t._tokenize()
    return t

#```


