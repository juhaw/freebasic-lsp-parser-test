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
                if self.current_char == '"':
                    self.advance()
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
                        else:
                            break
                    elif self.current_char.isdigit():
                        num += self.current_char
                    else:
                        break
                    self.advance()
                self.tokens.append(Token("NUMBER", num, self.line, start_col))
                continue

            # KORJAA TÄMÄ: Lisää #include-käsittely
            if char == '#':
                start_col = self.col
                directive = char
                self.advance()
                while self.current_char is not None and (self.current_char.isalpha() or self.current_char == '_'):
                    directive += self.current_char
                    self.advance()
                self.tokens.append(Token("DIRECTIVE", directive, self.line, start_col))
                continue

            if char.isalpha() or char == '_':
                start_col = self.col
                ident = ""
                while self.current_char is not None and (self.current_char.isalnum() or self.current_char == '_'):
                    ident += self.current_char
                    self.advance()

                if self.current_char is not None and self.current_char in "$%&!#":
                    ident += self.current_char
                    self.advance()

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
                self.tokens.append(Token("EQUAL", "=", self.line, self.col))
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
    def __init__(self, name):
        super().__init__("Type")
        self.name = name
        self.fields = []
        self.methods = []
        self.properties = []

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
    def __init__(self, decls):
        super().__init__("Dim")
        # decls = list of {"name": str, "type": str, "dims": list|None, "shared": bool, "static": bool}
        self.decls = decls

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
    def __str__(self):
        result = f"Type {self.name}:\n"
        for field in self.fields:
            static_mark = " (Static)" if getattr(field, "is_static", False) else ""
            result += f"  {field.name} : {field.type_name}{static_mark}\n"
        for method in self.methods:
            params = ", ".join([p[0] for p in method.params]) if method.params else ""
            result += f"  {method.name}({params})\n"
        return result

class VariableSymbol:
  
    def __init__(self, name, type_name, init_value=None, is_shared=False, is_static=False):
        self.name = name
        self.type = type_name
        self.init_value = init_value
        self.is_shared = is_shared
        self.is_static = is_static
    def __str__(self):
        result = f"{self.name} : {self.type}"
        if self.init_value:
            # Tulosta init_value siistimmin
            if self.init_value.get("type") == "string":
                result += f' = "{self.init_value.get("value")}"'
            elif self.init_value.get("type") == "number":
                result += f" = {self.init_value.get('value')}"
            elif self.init_value.get("type") == "constructor":
                args = ", ".join(self.init_value.get("args", []))
                result += f" = {self.init_value.get('name')}({args})"
            else:
                result += f" = {self.init_value}"
        if self.is_shared:
            result += " [Shared]"
        if self.is_static:
            result += " [Static]"
        return result

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

                m_name = getattr(m, 'name', 'Unknown')

                # Konstruktorit/destruktorit erikseen
                if m_name == "(" or isinstance(m, ConstructorDestructorNode):
                    m_name = ts.name  # Käytä tyypin nimeä

                # Luo parametrilista
                param_str = ""
                if hasattr(m, 'params') and m.params:
                    param_names = [p[0] for p in m.params]
                    param_str = f"({', '.join(param_names)})"
                else:
                    param_str = "()"

                members.append({
                    "label": m_name,
                    "insertText": f"{m_name}{param_str}",
                    "detail": f"(Method) {m_name}{param_str}"
                })
            result[ts.name] = members
        return result

    def var_to_type_dict(self):
        result = {}
        for name, vs in self.variables.items():
            result[vs.name] = {
                "type": vs.type,
                "init_value": getattr(vs, "init_value", None),
                "is_shared": getattr(vs, "is_shared", False),
                "is_static": getattr(vs, "is_static", False)
            }
        return result

class Parser:
    # Dataohjattu syntaksiperheiden määrittely
    grammar_table = {
        # IDENT-pohjaiset patternit
        ("IDENT", "as", "IDENT"): "parseVarDecl",
        ("dim", "IDENT", "as", "IDENT"): "parseDim",
        ("type", "IDENT"): "parseTypeBlock",
        ("declare", "function", "IDENT"): "parseGlobalDeclare",
        ("declare", "sub", "IDENT"): "parseGlobalDeclare"
    }

    def __init__(self, tokens, symbol_table=None, base_path=""):
        self.tokens = tokens
        self.pos = 0
        self.symbol_table = symbol_table if symbol_table else SymbolTable()
        self.base_path = base_path
        self.current_type = None

        # KeywordRegistry poistettu käytöstä
        # self.registry = KeywordRegistry.create_default_registry()

        # grammar_table säilyy ennallaan
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
        tok = self.current()

        # Pattern: IDENT AS IDENT  → var_decl
        if tok.type == "IDENT":
            nxt = self.peek()
            if nxt.type == "IDENT" and nxt.value.lower() == "as":
                return self.parseVarDecl()

        # Pattern: DIM IDENT AS IDENT
        if tok.type == "IDENT" and tok.value.lower() == "dim":
            return self.parseDim()

        # Pattern: TYPE IDENT
        if tok.type == "IDENT" and tok.value.lower() == "type":
            return self.parseTypeBlock()

        # Pattern: DECLARE FUNCTION/SUB IDENT
        if tok.type == "IDENT" and tok.value.lower() == "declare":
            return self.parseGlobalDeclare()

        return None


    def parseBlock(self):
        nodes = []
        while self.current().type != "EOF":
            start_pos = self.pos
            node = self.parseStatement()
            if node:
                nodes.append(node)
            if self.pos == start_pos:
                self.advance()
        return nodes

    def parseStatement(self):
        tok = self.current()

        if tok.type in ("DIRECTIVE", "IDENT"):
            handler_name = self.statement_dispatch.get(tok.value.lower())
            if handler_name:
                handler = getattr(self, handler_name, None)
                if handler:
                    result = handler()
                    if result is None:
                        line = tok.line
                        while self.current().type != "EOF" and self.current().line == line:
                            self.advance()
                    return result

        if tok.type == "IDENT":
            node = self.parseAssignment()
            if node:
                return node

            line = tok.line
            while self.current().type != "EOF" and self.current().line == line:
                self.advance()
            return None

        self.advance()
        return None

    def parseInclude(self):
        if not (self.current().type == "DIRECTIVE" and 
                self.current().value.lower() == "#include"):
            return None

        self.advance()

        path = ""
        if self.current().type == "STRING":
            path = self.current().value
            self.advance()
        elif (self.current().type == "IDENT" and 
              self.current().value == "<"):
            self.advance()
            while (self.current().type != "IDENT" or 
                   self.current().value != ">") and self.current().type != "EOF":
                path += self.current().value
                self.advance()
            if self.current().type == "IDENT" and self.current().value == ">":
                self.advance()
        else:
            return None

        full_path = os.path.join(self.base_path, path)
        if os.path.exists(full_path):
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                code = f.read()
            tokenizer = tokenize_source(code, full_path)
            sub_parser = Parser(tokenizer.get_tokens(), self.symbol_table, 
                               os.path.dirname(full_path))
            sub_parser.parseBlock()

        return IncludeNode(path)

    def _handle_type_declare(self, visibility, tnode, ts):
        self.advance()  # ohita 'declare'

        # Tarkista onko constructor/destructor
        next_tok = self.current()
        if next_tok.value.lower() in ("constructor", "destructor"):
            return self.handleConstructorDestructor(visibility, tnode)

        # ... vanha koodi jatkuu ...
        kind = self.current().value.lower()  # 'sub' tai 'function'
        self.advance()

        name = self.current().value
        self.advance()

        params = []
        if self.current().type == "LPAREN":
            self.advance()
            while self.current().type != "RPAREN":
                if self.current().type == "IDENT":
                    param_name = self.current().value
                    self.advance()
                    param_type = "Any"
                    if self.current().type == "IDENT" and self.current().value.lower() == "as":
                        self.advance()
                        if self.current().type == "IDENT":
                            param_type = self.current().value
                            self.advance()
                    params.append((param_name, param_type))
                if self.current().type == "COMMA":
                    self.advance()
            self.advance()

        return_type = "Void"
        if kind == "function" and self.current().type == "IDENT" and self.current().value.lower() == "as":
            self.advance()
            if self.current().type == "IDENT":
                return_type = self.current().value
                self.advance()

        # Luo MethodNode
        method = MethodNode(name, params, return_type, visibility)
        tnode.methods.append(method)
        ts.methods.append(method)

        return True, visibility

        # ... vanha koodi jatkuu ...

    def _handle_type_static(self, visibility, tnode):
        self.advance()  # ohita 'static'

        if self.current().type != "IDENT":
            return False, visibility

        field_name = self.current().value
        self.advance()

        if self.current().type != "IDENT" or self.current().value.lower() != "as":
            return False, visibility
        self.advance()

        if self.current().type != "IDENT":
            return False, visibility

        type_name = self.current().value
        self.advance()

        # Luo staattinen kenttä
        fnode = FieldNode(field_name, type_name, visibility, is_static=True)
        tnode.fields.append(fnode)

        return True, visibility

    def _handle_type_dim(self, visibility, tnode):
        self.advance()  # skip DIM

        is_static = False
        is_shared = False

        if self.current().type == "IDENT" and self.current().value.lower() in ("shared", "static"):
            if self.current().value.lower() == "shared":
                is_shared = True
            else:
                is_static = True
            self.advance()

        while True:
            if self.current().type != "IDENT":
                return True, visibility

            name = self.current().value
            self.advance()

            if self.current().type == "LPAREN":
                while self.current().type not in ("RPAREN", "EOF"):
                    self.advance()
                if self.current().type == "RPAREN":
                    self.advance()

            if self.current().type != "IDENT" or self.current().value.lower() != "as":
                return True, visibility
            self.advance()

            if self.current().type != "IDENT":
                return True, visibility
            type_name = self.current().value
            self.advance()

            fnode = FieldNode(name, type_name, visibility, is_static=is_static)
            tnode.fields.append(fnode)

            if self.current().type == "COMMA":
                self.advance()
                continue

            return True, visibility

    def _dispatch_type_block_line(self, visibility, tnode, ts):
        tok = self.current()
        key = tok.value.lower()

        # Visibility handlers
        if key in ("public", "private"):
            visibility = key
            self.advance()
            # Optional colon
            if self.current().type == "COLON":
                self.advance()
            return True, visibility

        # DIM inside TYPE
        if key == "dim":
            return self._handle_type_dim(visibility, tnode)

        # existing handlers
        handler_name = self.type_block_dispatch.get(key)
        if handler_name:
            handler = getattr(self, handler_name)
            # Kutsu handleria oikealla määrällä parametreja
            if handler_name == "_handle_type_declare":
                result = handler(visibility, tnode, ts)
            else:
                result = handler(visibility, tnode)
            if result is None:
                return False, visibility
            return result

        # fallback: normal field line
        return self._handle_type_field(visibility, tnode)

    def parseTypeBlock(self):
        tok = self.current()
        if tok.type != "IDENT" or tok.value.lower() != "type":
            return None

        self.advance()

        if self.current().type != "IDENT":
            return None

        type_name = self.current().value
        self.advance()

        tnode = TypeNode(type_name)
        current_visibility = "public"

        # Luo symboli
        ts = TypeSymbol(type_name, [], [])
        self.symbol_table.addType(ts)
        self.current_type = ts  # Aseta nykyinen tyyppi

        while True:
            tok = self.current()

            if tok.type == "EOF":
                break

            if tok.type == "IDENT" and tok.value.lower() == "end":
                nxt = self.peek()
                if nxt.type == "IDENT" and nxt.value.lower() == "type":
                    self.advance()  # end
                    self.advance()  # type
                    break

            # Kutsu dispatch-metodia TS:llä
            handled, current_visibility = self._dispatch_type_block_line(current_visibility, tnode, ts)
            if handled:
                # Synkronoi
                ts.fields = tnode.fields.copy()
                ts.methods = tnode.methods.copy()
            else:
                self.advance()

        self.current_type = None  # Nollaa nykyinen tyyppi
        return tnode

    def parsePlainField(self, visibility):
        tok = self.current()

        if tok.type != "IDENT":
            return None

        field_name = tok.value
        self.advance()

        tok = self.current()
        if tok.type != "IDENT" or tok.value.lower() != "as":
            return None

        self.advance()

        tok = self.current()
        if tok.type != "IDENT":
            return None

        type_name = tok.value
        self.advance()

        fnode = FieldNode(field_name, type_name, visibility)

        # 🔥 VAIN YKSI LISÄYS — EI TUPLA-APPENDEJA
        return fnode

    def parseTypeMethod(self, visibility="public"):
        pass

    def parseParameters(self):
        pass

    def parseDim(self):
        start_pos = self.pos
        if not (self.current().type == "IDENT" and self.current().value.lower() == "dim"):
            return None
        self.advance()
        is_shared = False
        is_static = False
        if self.current().type == "IDENT":
            if self.current().value.lower() == "shared":
                is_shared = True
                self.advance()
            elif self.current().value.lower() == "static":
                is_static = True
                self.advance()
        decls = []
        while True:
            if self.current().type != "IDENT":
                if decls:
                    break
                self.pos = start_pos
                return None
            name = self.current().value
            self.advance()
            dims = None
            if self.current().type == "LPAREN":
                dims = self._parseArrayDimensions()
            if not (self.current().type == "IDENT" and self.current().value.lower() == "as"):
                self.pos = start_pos
                return None
            self.advance()
            if self.current().type != "IDENT":
                self.pos = start_pos
                return None
            type_name = self.current().value
            self.advance()
            init_value = None
            if self.current().type == "EQUAL":
                self.advance()
                init_value = self._parseInitializer()
            decl = {
                "name": name,
                "type": type_name,
                "dims": dims,
                "init": init_value,
                "shared": is_shared,
                "static": is_static
            }
            decls.append(decl)
            # KÄYTÄ NYT KAIKKIA PARAMETREJA!
            self.symbol_table.addVariable(VariableSymbol(
                name, type_name, init_value, is_shared, is_static
            ))
            if self.current().type != "COMMA":
                break
            self.advance()
        return DimNode(decls)

    def parseStaticField(self, visibility):
        tok = self.current()

        # Odotetaan IDENT, jonka arvo on "static"
        if tok.type != "IDENT" or tok.value.lower() != "static":
            return None

        self.advance()

        # Odotetaan kentän nimi (IDENT)
        tok = self.current()
        if tok.type != "IDENT":
            return None

        field_name = tok.value
        self.advance()

        # Odotetaan "as"
        tok = self.current()
        if tok.type != "IDENT" or tok.value.lower() != "as":
            return None

        self.advance()

        # Odotetaan tyyppinimi (IDENT)
        tok = self.current()
        if tok.type != "IDENT":
            return None

        type_name = tok.value
        self.advance()

        fnode = StaticFieldNode(field_name, type_name, visibility)
        return fnode

    def parseVarDecl(self):
        # IDENT
        if self.current().type != "IDENT":
            return None
        name = self.current().value
        self.advance()

        # AS
        if self.current().type != "IDENT" or self.current().value.lower() != "as":
            return None
        self.advance()

        # IDENT (type)
        if self.current().type != "IDENT":
            return None
        type_name = self.current().value
        self.advance()

        return VarDeclNode(name, type_name)

    def parseExpr(self):
        tok = self.current()
        if tok.type in ("NUMBER", "IDENT"):
            val = tok.value
            self.advance()
            return {"kind": "Expr", "value": val}
        return None
    
    def parseAssignment(self):
        tok = self.current()

        # Vasemman puolen alku: ident tai pisteketju / array
        if tok.type != "IDENT":
            return None

        left_tokens = []
        left_tokens.append(tok.value)
        self.advance()

        # Mahdollinen array- tai pisteketju: myvar(0).field
        while True:
            tok = self.current()
            if tok.type in ("DOT", "LPAREN"):
                left_tokens.append(tok.value)
                self.advance()
            elif tok.type in ("NUMBER", "IDENT", "RPAREN", "COMMA"):
                left_tokens.append(tok.value)
                self.advance()
            else:
                break

        # Odotetaan "=" (EQUAL)
        tok = self.current()
        if tok.type != "EQUAL":
            return None
        self.advance()

        # Oikea puoli: yksinkertainen arvo (IDENT, NUMBER, STRING)
        tok = self.current()
        if tok.type not in ("IDENT", "NUMBER", "STRING"):
            return None

        right_value = tok.value
        self.advance()

        left_repr = "".join(str(x) for x in left_tokens)
        node = AssignmentNode(left_repr, right_value)
        return node
    def consume(self):
        tok = self.current()
        self.advance()
        return tok
    def parseMethodImplementation(self):
        tok = self.current()

        if tok.type != "IDENT" or tok.value.lower() not in ("function", "sub"):
            return None

        kind = tok.value.lower()
        self.advance()

        if self.current().type != "IDENT":
            return None

        name = self.current().value
        self.advance()

        params = []
        if self.current().type == "LPAREN":
            self.advance()
            while self.current().type != "RPAREN":
                if self.current().type != "IDENT":
                    return None
                params.append(self.current().value)
                self.advance()
                if self.current().type == "COMMA":
                    self.advance()
            self.advance()

        return_type = None
        if kind == "function":
            if self.current().type == "IDENT" and self.current().value.lower() == "as":
                self.advance()
                if self.current().type != "IDENT":
                    return None
                return_type = self.current().value
                self.advance()

        body = []
        while True:
            start_pos = self.pos
            tok = self.current()

            if tok.type == "IDENT" and tok.value.lower() == "end":
                nxt = self.peek()
                if nxt.type == "IDENT" and nxt.value.lower() == kind:
                    self.advance()
                    self.advance()
                    break

            stmt = self.parseStatement()
            if stmt:
                body.append(stmt)
            else:
                self.advance()

            if self.pos == start_pos:
                self.advance()
                break

        node = MethodNode(name, params, return_type)
        return node
    def _handle_type_property(self, visibility, tnode):
        self.advance()  # ohita 'property'

        if self.current().type != "IDENT":
            return False, visibility

        name = self.current().value
        self.advance()

        if self.current().type != "IDENT" or self.current().value.lower() != "as":
            return False, visibility
        self.advance()

        if self.current().type != "IDENT":
            return False, visibility

        type_name = self.current().value
        self.advance()

        # Luo PropertyNode
        prop_node = PropertyNode(name, type_name, visibility, [], [])
        tnode.properties.append(prop_node)

        # Skipataan propertyn runko toistaiseksi
        while self.current().type != "EOF":
            if self.current().type == "IDENT" and self.current().value.lower() == "end":
                nxt = self.peek()
                if nxt.type == "IDENT" and nxt.value.lower() == "property":
                    self.advance()  # end
                    self.advance()  # property
                    break
            self.advance()

        return True, visibility
    def parseGlobalDeclare(self):
        tok = self.current()

        # Odotetaan IDENT, jonka arvo on "declare"
        if tok.type != "IDENT" or tok.value.lower() != "declare":
            return None

        self.advance()

        # Odotetaan "function" tai "sub"
        tok = self.current()
        if tok.type != "IDENT" or tok.value.lower() not in ("function", "sub"):
            return None

        kind = tok.value.lower()
        self.advance()

        # Odotetaan nimi
        if self.current().type != "IDENT":
            return None

        name = self.current().value
        self.advance()

        # Parametrit (valinnaiset)
        params = []
        if self.current().type == "LPAREN":
            self.advance()
            while self.current().type != "RPAREN":
                if self.current().type != "IDENT":
                    return None
                params.append(self.current().value)
                self.advance()
                if self.current().type == "COMMA":
                    self.advance()
            self.advance()

        # Palautustyyppi (vain Function)
        return_type = None
        if kind == "function":
            if self.current().type == "IDENT" and self.current().value.lower() == "as":
                self.advance()
                if self.current().type != "IDENT":
                    return None
                return_type = self.current().value
                self.advance()

        node = GlobalDeclareNode(kind, name, params, return_type)
        return node
    def handleConstructorDestructor(self, visibility, tnode):
        kind_tok = self.current()
        kind = kind_tok.value.lower()
        self.advance()

        type_name = tnode.name
        params = []

        if self.current().type == "LPAREN":
            self.advance()
            while self.current().type != "RPAREN" and self.current().type != "EOF":
                if self.current().type == "IDENT":
                    pname = self.current().value
                    self.advance()
                    ptype = "Any"
                    if self.current().type == "IDENT" and self.current().value.lower() == "as":
                        self.advance()
                        if self.current().type == "IDENT":
                            ptype = self.current().value
                            self.advance()
                    params.append((pname, ptype))
                else:
                    self.advance()
            if self.current().type == "RPAREN":
                self.advance()

        method_name = f"{kind.capitalize()} {type_name}"
        method_node = MethodNode(type_name, params, "Void", visibility)
        method_node.is_constructor = (kind == "constructor")
        method_node.is_destructor = (kind == "destructor")

        ts = self.symbol_table.getType(type_name)
        if ts:
            ts.methods = [m for m in ts.methods if not (
                (kind == "constructor" and getattr(m, "is_constructor", False)) or
                (kind == "destructor" and getattr(m, "is_destructor", False))
            )]
            ts.methods.append(method_node)

        tnode.methods = [m for m in tnode.methods if not (
            (kind == "constructor" and getattr(m, "is_constructor", False)) or
            (kind == "destructor" and getattr(m, "is_destructor", False))
        )]
        tnode.methods.append(method_node)

        return True, visibility
    def _handle_dim(self, is_shared=False):
        pass
    def parseTypeDeclaration(self):
        self.expect("KEYWORD", "type")
        type_name = self.expect("IDENT").value

        self.current_type = type_name
        self.symbol_table.addType(type_name)

        fields = []
        methods = []

        while self.current().type != "EOF":
            if self.current().value.lower() == "end":
                if self.peek(1) and self.peek(1).value.lower() == "type":
                    break

            if self.match("KEYWORD", "declare"):
                method_node = self.parseMethodImplementation()
                methods.append(method_node)
            elif self.current().type == "IDENT":
                field_name = self.advance().value
                self.expect("KEYWORD", "as")
                field_type = self.expect("IDENT").value
                fields.append((field_name, field_type))
                self.symbol_table.addVariable(VariableSymbol(field_name, field_type, type_name))
            else:
                self.advance()

        type_node = TypeNode(type_name, fields, methods)

        if self.match("KEYWORD", "end"):
            if self.match("KEYWORD", "type"):
                self.current_type = None
                return type_node

        self.current_type = None
        return type_node
    statement_dispatch = {
        "#include": "parseInclude",
        "type": "parseTypeBlock", 
        "dim": "parseDim",
        "function": "parseMethodImplementation",
        "sub": "parseMethodImplementation",
        "declare": "parseGlobalDeclare",
        "constructor": "parseMethodImplementation",
        "destructor": "parseMethodImplementation"
    }
    type_block_dispatch = {
        "declare": "_handle_type_declare",
        "static": "_handle_type_static",
        "dim": "_handle_type_dim",
        "property": "_handle_type_property",
        "constructor": "handleConstructorDestructor",
        "destructor": "handleConstructorDestructor",
        "public": "_handle_visibility",
        "private": "_handle_visibility"
    }
    def parseProperty(self, visibility, tnode):
        tok = self.current()

        if tok.type != "IDENT" or tok.value.lower() != "property":
            return None

        self.advance()

        if self.current().type != "IDENT":
            return None

        name = self.current().value
        self.advance()

        if self.current().type != "IDENT" or self.current().value.lower() != "as":
            return None

        self.advance()

        if self.current().type != "IDENT":
            return None

        type_name = self.current().value
        self.advance()

        getters = []
        setters = []

        while True:
            start_pos = self.pos
            tok = self.current()

            if tok.type == "IDENT" and tok.value.lower() == "end":
                nxt = self.peek()
                if nxt.type == "IDENT" and nxt.value.lower() == "property":
                    self.advance()
                    self.advance()
                    break

            if tok.type == "IDENT" and tok.value.lower() == "get":
                self.advance()
                stmt = self.parseStatement()
                if stmt:
                    getters.append(stmt)
                else:
                    self.advance()
            elif tok.type == "IDENT" and tok.value.lower() == "set":
                self.advance()
                stmt = self.parseStatement()
                if stmt:
                    setters.append(stmt)
                else:
                    self.advance()
            else:
                self.advance()

            if self.pos == start_pos:
                self.advance()
                break

        node = PropertyNode(name, type_name, visibility, getters, setters)
        tnode.properties.append(node)
        return True, visibility
    def parseEndBlock(self, kind):
        # Odotetaan "end <kind>"
        if self.current().type != "IDENT" or self.current().value.lower() != "end":
            return False

        nxt = self.peek()
        if nxt.type != "IDENT" or nxt.value.lower() != kind:
            return False

        self.advance()
        self.advance()
        return True
    def _handle_type_field(self, visibility, tnode):
        # name
        if self.current().type != "IDENT":
            return False, visibility
        name = self.current().value
        self.advance()

        # skip array dims
        if self.current().type == "LPAREN":
            while self.current().type not in ("RPAREN", "EOF"):
                self.advance()
            if self.current().type == "RPAREN":
                self.advance()

        # AS
        if self.current().type != "IDENT" or self.current().value.lower() != "as":
            return False, visibility
        self.advance()

        # type name
        if self.current().type != "IDENT":
            return False, visibility
        type_name = self.current().value
        self.advance()

        # add field
        fnode = FieldNode(name, type_name, visibility, is_static=False)
        tnode.fields.append(fnode)

        return True, visibility
    def _handle_visibility(self, visibility, tnode):
        # Tämä käsitellään jo _dispatch_type_block_line:ssa
        # Palauta vain uusi visibility
        new_vis = self.current().value.lower()
        self.advance()
        if self.current().type == "COLON":
            self.advance()
        return True, new_vis
    def _parseArrayDimensions(self):
        if self.current().type != "LPAREN":
            return None
        self.advance()
        dims = []
        while self.current().type != "RPAREN" and self.current().type != "EOF":
            lower = None
            upper = None
            if self.current().type in ("NUMBER", "IDENT"):
                lower = self.current().value
                self.advance()
                if (self.current().type == "IDENT" and 
                    self.current().value.lower() == "to"):
                    self.advance()
                    if self.current().type in ("NUMBER", "IDENT"):
                        upper = self.current().value
                        self.advance()
                else:
                    upper = lower
                    lower = "0"
            if lower is not None:
                dims.append((lower, upper))
            if self.current().type == "COMMA":
                self.advance()
            elif self.current().type == "RPAREN":
                break
        if self.current().type == "RPAREN":
            self.advance()
        return dims
    def _parseInitializer(self):
        if self.current().type == "STRING":
            value = self.current().value
            self.advance()
            return {"type": "string", "value": value}
        elif self.current().type == "NUMBER":
            value = self.current().value
            self.advance()
            return {"type": "number", "value": value}
        elif self.current().type == "IDENT":
            value = self.current().value
            self.advance()
            if self.current().type == "LPAREN":
                self.advance()
                args = []
                while self.current().type != "RPAREN" and self.current().type != "EOF":
                    if self.current().type in ("NUMBER", "STRING", "IDENT"):
                        args.append(self.current().value)
                        self.advance()
                    if self.current().type == "COMMA":
                        self.advance()
                if self.current().type == "RPAREN":
                    self.advance()
                return {"type": "constructor", "name": value, "args": args}
            return {"type": "variable", "value": value}
        return None



def tokenize_source(source, filename=""):
    # KeywordRegistry ei ole enää käytössä
    t = Tokenizer(source, filename)
    t._tokenize()
    return t

#```

class IncludeNode(ASTNode):
    def __init__(self, path):
        super().__init__("Include")
        self.path = path

class StaticFieldNode(ASTNode):
    def __init__(self, name, type_name, visibility="public"):
        super().__init__("StaticField")
        self.name = name
        self.type_name = type_name
        self.visibility = visibility

class VarDeclNode(ASTNode):
    def __init__(self, name, type_name):
        super().__init__("VarDecl")
        self.name = name
        self.type_name = type_name

class GlobalDeclareNode(ASTNode):
    def __init__(self, kind, name, params, return_type):
        super().__init__("GlobalDeclare")
        self.kind = kind
        self.name = name
        self.params = params
        self.return_type = return_type

class ConstructorDestructorNode(ASTNode):
    def __init__(self, kind, type_name, visibility, body):
        super().__init__("CtorDtor")
        self.kind = kind                  # "constructor" tai "destructor"
        self.name = type_name             # TYYPIN nimi (esim. "Kangaroo")
        self.visibility = visibility
        self.body = body

        # 🔥 Lisätty, jotta testikoodi EI kaadu
        self.return_type = None
        self.params = []

class PropertyNode(ASTNode):
    def __init__(self, name, type_name, visibility, getters, setters):
        super().__init__("Property")
        self.name = name
        self.type_name = type_name
        self.visibility = visibility
        self.getters = getters
        self.setters = setters
