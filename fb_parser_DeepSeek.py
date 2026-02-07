#!/usr/bin/env python3
"""
FreeBASIC Parser with Visitor Pattern - Refaktoroitu versio
Yhdenmukaistettu parametrien käsittely
"""

import os
import re
from typing import List, Dict, Any, Optional, Union, Tuple
from abc import ABC, abstractmethod
from dataclasses import dataclass

# ==================== PARAMETER-LUOKKA (UUSI) ====================

@dataclass
class Parameter:
    """Yksittäinen funktion/metodin parametri"""
    name: str
    type_name: str = "Any"
    is_byref: bool = False
    is_byval: bool = False
    is_optional: bool = False
    default_value: Any = None
    
    def __repr__(self):
        result = ""
        if self.is_byref:
            result += "ByRef "
        elif self.is_byval:
            result += "ByVal "
        if self.is_optional:
            result += "Optional "
        
        result += self.name
        if self.type_name != "Any":
            result += f" As {self.type_name}"
        if self.default_value is not None:
            if isinstance(self.default_value, str):
                result += f' = "{self.default_value}"'
            else:
                result += f" = {self.default_value}"
        return result
    
    def to_dict(self):
        """LSP-yhteensopiva dict"""
        return {
            "name": self.name,
            "type": self.type_name,
            "byref": self.is_byref,
            "byval": self.is_byval,
            "optional": self.is_optional,
            "default": self.default_value
        }


# ==================== TOKENIZER (pysyy samana) ====================

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
        self.pos += 1
        if self.pos < len(self.source):
            self.current_char = self.source[self.pos]
            self.col += 1
        else:
            self.current_char = None

    def peek(self):
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

            # Lohkokommentin alku (/' ... '/)
            if char == '/' and self.peek() == "'":
                self.advance()  # /
                self.advance()  # '
                # Etsi loppu ('/)
                while (self.current_char is not None and 
                       not (self.current_char == "'" and self.peek() == "/")):
                    if self.current_char == '\n':
                        self.line += 1
                        self.col = 1
                    self.advance()
                if self.current_char == "'" and self.peek() == "/":
                    self.advance()  # '
                    self.advance()  # /
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


# ==================== AST NODE TIETOTYYPIT ====================

class ASTNode(ABC):
    """Kaikkien nodejen perusluokka"""
    @property
    @abstractmethod
    def kind(self) -> str:
        pass
    
    @abstractmethod
    def accept(self, visitor: 'ASTVisitor') -> Any:
        """Hyväksy vierailijan"""
        pass
    
    def get_children(self) -> List['ASTNode']:
        """Palauta kaikki lapsinodet (ylikirjoitetaan tarvittaessa)"""
        return []


# ==================== KONKREETTISET NODET (PÄIVITETTY) ====================

class ProgramNode(ASTNode):
    """Pääroot-node joka sisältää kaikki parsitut nodet"""
    def __init__(self, statements: List[ASTNode]):
        self.statements = statements
    
    @property
    def kind(self) -> str:
        return "Program"
    
    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_ProgramNode(self)
    
    def get_children(self) -> List[ASTNode]:
        return self.statements


class TypeNode(ASTNode):
    """TYPE nimi ... END TYPE"""
    def __init__(self, name: str):
        self.name = name  # Oletetaan jo normalisoitu
        self.fields: List[FieldNode] = []
        self.methods: List[MethodNode] = []
        self.properties: List[PropertyNode] = []
    
    @property
    def kind(self) -> str:
        return "Type"
    
    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_TypeNode(self)
    
    def get_children(self) -> List[ASTNode]:
        children = []
        children.extend(self.fields)
        children.extend(self.methods)
        children.extend(self.properties)
        return children


class FieldNode(ASTNode):
    """Kenttä type sisällä"""
    def __init__(self, name: str, type_name: str, visibility: str = "public", is_static: bool = False):
        self.name = name  # Oletetaan jo normalisoitu
        self.type_name = type_name  # Oletetaan jo normalisoitu
        self.visibility = visibility  # Oletetaan jo normalisoitu
        self.is_static = is_static
    
    @property
    def kind(self) -> str:
        return "Field"
    
    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_FieldNode(self)


class MethodNode(ASTNode):
    """Metodi type sisällä (PÄIVITETTY)"""
    def __init__(self, name: str, params: List[Parameter], return_type: str, visibility: str = "public"):
        self.name = name
        self.params = params  # Nyt List[Parameter]
        self.return_type = return_type
        self.visibility = visibility
        self.is_constructor = False
        self.is_destructor = False
    
    @property
    def kind(self) -> str:
        return "Method"
    
    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_MethodNode(self)
    
    def get_param_string(self) -> str:
        """Palauttaa parametrilistan merkkijonona"""
        param_strs = []
        for param in self.params:
            param_desc = str(param)
            param_strs.append(param_desc)
        return ", ".join(param_strs)


class DimNode(ASTNode):
    """DIM määritys"""
    def __init__(self, decls: List[Dict[str, Any]]):
        self.decls = decls
    
    @property
    def kind(self) -> str:
        return "Dim"
    
    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_DimNode(self)
    
    def __repr__(self):
        return f"DimNode({len(self.decls)} declarations)"


class AssignmentNode(ASTNode):
    """Sijoituslause"""
    def __init__(self, target: str, value: str):
        self.target = target
        self.value = value
    
    @property
    def kind(self) -> str:
        return "Assignment"
    
    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_AssignmentNode(self)
    
    def __repr__(self):
        return f"Assignment({self.target} = {self.value})"


class IncludeNode(ASTNode):
    """#include direktiivi"""
    def __init__(self, path: str):
        self.path = path
    
    @property
    def kind(self) -> str:
        return "Include"
    
    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_IncludeNode(self)


class StaticFieldNode(ASTNode):
    """Staattinen kenttä type sisällä"""
    def __init__(self, name: str, type_name: str, visibility: str = "public"):
        self.name = name
        self.type_name = type_name
        self.visibility = visibility
    
    @property
    def kind(self) -> str:
        return "StaticField"
    
    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_StaticFieldNode(self)


class VarDeclNode(ASTNode):
    """Yksinkertainen muuttujan määritys (IDENT AS IDENT)"""
    def __init__(self, name: str, type_name: str):
        self.name = name
        self.type_name = type_name
    
    @property
    def kind(self) -> str:
        return "VarDecl"
    
    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_VarDeclNode(self)


class GlobalDeclareNode(ASTNode):
    """DECLARE FUNCTION/SUB (PÄIVITETTY)"""
    def __init__(self, kind: str, name: str, params: List[Parameter], return_type: Optional[str]):
        self.kind = kind  # "function" tai "sub"
        self.name = name
        self.params = params  # Nyt List[Parameter]
        self.return_type = return_type
    
    @property
    def kind(self) -> str:
        return "GlobalDeclare"
    
    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_GlobalDeclareNode(self)
    
    def get_param_string(self) -> str:
        """Palauttaa parametrilistan merkkijonona"""
        param_strs = []
        for param in self.params:
            param_desc = str(param)
            param_strs.append(param_desc)
        return ", ".join(param_strs)


class ConstructorDestructorNode(ASTNode):
    """Konstruktori tai destruktori type sisällä (PÄIVITETTY)"""
    def __init__(self, kind: str, type_name: str, visibility: str = "public", body: List[ASTNode] = None):
        self._kind = kind  # Tallenna privaattina
        self.name = type_name  # TYYPIN nimi
        self.visibility = visibility
        self.body = body or []
        self.params: List[Parameter] = []  # Nyt List[Parameter]

    @property
    def kind(self) -> str:
        return self._kind

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_ConstructorDestructorNode(self)

    def get_children(self) -> List[ASTNode]:
        return self.body


class PropertyNode(ASTNode):
    """Property type sisällä"""
    def __init__(self, name: str, type_name: str, visibility: str, 
                 getters: List[ASTNode], setters: List[ASTNode]):
        self.name = name
        self.type_name = type_name
        self.visibility = visibility
        self.getters = getters
        self.setters = setters
    
    @property
    def kind(self) -> str:
        return "Property"
    
    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_PropertyNode(self)
    
    def get_children(self) -> List[ASTNode]:
        return self.getters + self.setters


# ==================== VISITOR INTERFACE ====================

class ASTVisitor(ABC):
    """Visitor perusluokka"""
    
    @abstractmethod
    def visit(self, node: ASTNode) -> Any:
        """Vieraile nodessa"""
        pass
    
    def generic_visit(self, node: ASTNode) -> Any:
        """Oletusmetodi jos tiettyä visit_-metodia ei ole"""
        for child in node.get_children():
            child.accept(self)
        return None


class BaseVisitor(ASTVisitor):
    """Perusvisitori joka automaattisesti kutsuu oikeita metodeja"""
    
    def visit(self, node: ASTNode) -> Any:
        method_name = f'visit_{node.kind}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)


# ==================== SYMBOL TABLE (PÄIVITETTY) ====================

class TypeSymbol:
    def __init__(self, name: str, fields: List[FieldNode], methods: List[MethodNode]):
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
            param_str = method.get_param_string()
            method_type = ""
            if getattr(method, "is_constructor", False):
                method_type = "Constructor "
            elif getattr(method, "is_destructor", False):
                method_type = "Destructor "
            result += f"  {method_type}{method.name}({param_str})"
            if method.return_type and method.return_type != "Void":
                result += f" As {method.return_type}"
            result += "\n"
        return result


class VariableSymbol:
    def __init__(self, name: str, type_name: str, init_value: Any = None, 
                 is_shared: bool = False, is_static: bool = False):
        self.name = name.lower()  # NORMALISOI
        self.type = type_name.lower()  # NORMALISOI
        self.init_value = init_value
        self.is_shared = is_shared
        self.is_static = is_static
    
    def __str__(self):
        result = f"{self.name} : {self.type}"
        if self.init_value:
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
        self.types: Dict[str, TypeSymbol] = {}
        self.variables: Dict[str, VariableSymbol] = {}
    
    def addType(self, type_symbol: TypeSymbol) -> None:
        lower_name = type_symbol.name.lower()

        if lower_name in self.types:
            existing = self.types[lower_name]
            # Voi tulostaa varoituksen
            print(f"Warning: Type '{type_symbol.name}' redefined (originally '{existing.name}')")

        self.types[lower_name] = type_symbol
        # Tallenna alkuperäinen nimi
        if not hasattr(self, '_original_names'):
            self._original_names = {}
        self._original_names[lower_name] = type_symbol.name
    
    def addVariable(self, var_symbol: VariableSymbol) -> None:
        self.variables[var_symbol.name.lower()] = var_symbol
    
    def getType(self, name: str) -> Optional[TypeSymbol]:
        if name is None:
            return None
        return self.types.get(name.lower())
    
    def getVariable(self, name: str) -> Optional[VariableSymbol]:
        if name is None:
            return None
        return self.variables.get(name.lower())
    
    def all_types_dict(self) -> Dict[str, List[Dict[str, str]]]:
        """LSP-autocompleteen"""
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
                
                method_type = ""
                if getattr(m, "is_constructor", False):
                    method_type = "Constructor "
                elif getattr(m, "is_destructor", False):
                    method_type = "Destructor "

                param_text = m.get_param_string()
                
                members.append({
                    "label": f"{method_type}{m.name}",
                    "insertText": f"{m.name}({param_text})",
                    "detail": f"({method_type}Method) {m.name}({param_text})"
                })
            result[ts.name] = members
        return result
    
    def var_to_type_dict(self) -> Dict[str, Dict[str, Any]]:
        """LSP-hover-tietoihin"""
        result = {}
        for name, vs in self.variables.items():
            result[vs.name] = {
                "type": vs.type,
                "init_value": getattr(vs, "init_value", None),
                "is_shared": getattr(vs, "is_shared", False),
                "is_static": getattr(vs, "is_static", False)
            }
        return result


# ==================== SYMBOL COLLECTOR VISITOR (PÄIVITETTY) ====================

class SymbolCollectorVisitor(BaseVisitor):
    """Kerää symbolit AST:stä SymbolTableen"""
    
    def __init__(self):
        super().__init__()
        self.symbol_table = SymbolTable()
        self._context_stack: List[Tuple[str, str]] = []  # (context_type, name)
    
    @property
    def _current_context(self) -> Optional[str]:
        return self._context_stack[-1][0] if self._context_stack else None
    
    def visit_ProgramNode(self, node: ProgramNode) -> None:
        for stmt in node.statements:
            stmt.accept(self)
    
    def visit_TypeNode(self, node: TypeNode) -> None:
        ts = TypeSymbol(node.name, node.fields.copy(), [])

        method_nodes = [m for m in node.methods if isinstance(m, MethodNode)]
        for method in method_nodes:
            existing = [m for m in ts.methods if m.name == method.name]
            if not existing:
                ts.methods.append(method)

        self.symbol_table.addType(ts)
        self._context_stack.append(("type", node.name))

        for field in node.fields:
            field.accept(self)

        ctor_dtor_nodes = [m for m in node.methods if isinstance(m, ConstructorDestructorNode)]
        for ctor_dtor in ctor_dtor_nodes:
            ctor_dtor.accept(self)

        for prop in node.properties:
            prop.accept(self)

        self._context_stack.pop()
    
    def visit_FieldNode(self, node: FieldNode) -> None:
        if self._current_context == "type":
            type_name = self._context_stack[-1][1]
            ts = self.symbol_table.getType(type_name)
            if ts:
                existing = [f for f in ts.fields if f.name == node.name]
                if not existing:
                    ts.fields.append(node)
    
    def visit_MethodNode(self, node: MethodNode) -> None:
        if self._current_context == "type":
            type_name = self._context_stack[-1][1]
            ts = self.symbol_table.getType(type_name)
            if ts:
                existing = [m for m in ts.methods if m.name == node.name]
                if not existing:
                    ts.methods.append(node)
    
    def visit_DimNode(self, node: DimNode) -> None:
        for decl in node.decls:
            var_sym = VariableSymbol(
                decl['name'],
                decl['type'],
                decl.get('init'),
                decl.get('shared', False),
                decl.get('static', False)
            )
            self.symbol_table.addVariable(var_sym)
    
    def visit_AssignmentNode(self, node: AssignmentNode) -> None:
        pass
    
    def visit_IncludeNode(self, node: IncludeNode) -> None:
        pass
    
    def visit_StaticFieldNode(self, node: StaticFieldNode) -> None:
        self.visit_FieldNode(node)
    
    def visit_VarDeclNode(self, node: VarDeclNode) -> None:
        var_sym = VariableSymbol(node.name, node.type_name)
        self.symbol_table.addVariable(var_sym)
    
    def visit_GlobalDeclareNode(self, node: GlobalDeclareNode) -> None:
        type_str = f"{node.kind.capitalize()}"
        if node.return_type:
            type_str += f"[{node.return_type}]"
        var_sym = VariableSymbol(node.name, type_str)
        self.symbol_table.addVariable(var_sym)
    
    def visit_ConstructorDestructorNode(self, node: ConstructorDestructorNode) -> None:
        if self._current_context == "type":
            type_name = self._context_stack[-1][1]
            ts = self.symbol_table.getType(type_name)
            if ts:
                existing_ctor = any(
                    isinstance(m, MethodNode) and m.is_constructor 
                    for m in ts.methods
                )
                existing_dtor = any(
                    isinstance(m, MethodNode) and m.is_destructor 
                    for m in ts.methods
                )

                if node.kind == "constructor" and not existing_ctor:
                    method_node = MethodNode(
                        type_name,
                        node.params,
                        "Void",
                        node.visibility
                    )
                    method_node.is_constructor = True
                    ts.methods.append(method_node)

                elif node.kind == "destructor" and not existing_dtor:
                    method_node = MethodNode(
                        type_name,
                        node.params,
                        "Void",
                        node.visibility
                    )
                    method_node.is_destructor = True
                    ts.methods.append(method_node)
    
    def visit_PropertyNode(self, node: PropertyNode) -> None:
        pass


# ==================== PARSER (PÄIVITETTY - YHDENMUUKAISTETTU) ====================

class Parser:
    """FreeBASIC-parseri (yhdenmukaistettu parametrien käsittely)"""
    
    def __init__(self, tokens, base_path=""):
        self.tokens = tokens
        self.pos = 0
        self.base_path = base_path
        self.current_type = None

        self.statement_dispatch = {
            "#include": "parseInclude",
            "type": "parseTypeBlock", 
            "dim": "parseDim",
            "shared": "parseDim",  # Shared käsitellään samalla funktiolla kuin DIM
            "function": "parseMethodImplementation",
            "sub": "parseMethodImplementation",
            "declare": "parseGlobalDeclare",
            "constructor": "parseMethodImplementation",
            "destructor": "parseMethodImplementation",
            "print": "parsePrintStatement",
        }

        self.type_block_dispatch = {
            "declare": "_handle_type_declare",
            "static": "_handle_type_static",
            "dim": "_handle_type_dim",
            "property": "_handle_type_property",
            "constructor": "handleConstructorDestructor",
            "destructor": "handleConstructorDestructor",
            "public": "_handle_visibility",
            "private": "_handle_visibility"
        }
    
    def current(self) -> Token:
        return self.tokens[self.pos]
    
    def peek(self, offset: int = 1) -> Token:
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return Token("EOF", "", self.current().line, self.current().column)
    
    def advance(self) -> Token:
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return self.current()
    
    def match(self, type_: str, value: str = None) -> bool:
        tok = self.current()
        if tok.type == type_ and (value is None or tok.value.lower() == value.lower()):
            self.advance()
            return True
        return False
    
    def expect(self, type_: str, value: str = None) -> Token:
        tok = self.current()
        if tok.type == type_ and (value is None or tok.value.lower() == value.lower()):
            self.advance()
            return tok
        raise SyntaxError(f"Expected {type_} '{value}' at line {tok.line}, got {tok.type} '{tok.value}'")
    
    # ========== YHTEINEN PARAMETRILISTAN PARSERI ==========
    
    def _parse_parameter_list(self) -> List[Parameter]:
        """Parsii parametrilistan suluista"""
        params = []

        if not self.match("LPAREN"):
            return params

        # Tyhjä parametrilista?
        if self.match("RPAREN"):
            return params

        while True:
            # Tarkista BYREF/BYVAL
            is_byref = False
            is_byval = False
            is_optional = False

            if self.current().type == "IDENT":
                ident_lower = self.current().value.lower()
                if ident_lower == "byref":
                    is_byref = True
                    self.advance()
                elif ident_lower == "byval":
                    is_byval = True
                    self.advance()
                elif ident_lower == "optional":
                    is_optional = True
                    self.advance()

            # Parametrin nimi
            if self.current().type != "IDENT":
                # Poikkeus käsittely
                while self.current().type != "RPAREN" and self.current().type != "COMMA" and self.current().type != "EOF":
                    self.advance()
                if self.current().type == "COMMA":
                    self.advance()
                    continue
                else:
                    break

            param_name = self._normalize_identifier(self.current().value)
            self.advance()

            # Parametrin tyyppi
            param_type = "Any"
            if self.current().type == "IDENT" and self.current().value.lower() == "as":
                self.advance()
                if self.current().type == "IDENT":
                    param_type = self._normalize_identifier(self.current().value)
                    self.advance()

            # Oletusarvo
            default_value = None
            if self.current().type == "EQUAL":
                self.advance()
                default_value = self._parse_simple_value()

            # Luo Parameter-olio
            param = Parameter(
                name=param_name,
                type_name=param_type,
                is_byref=is_byref,
                is_byval=is_byval,
                is_optional=is_optional,
                default_value=default_value
            )
            params.append(param)

            # Jatka jos on pilkku
            if not self.match("COMMA"):
                break

        # Sulje sulut
        if not self.match("RPAREN"):
            # Yritä löytää sulku
            while self.current().type != "RPAREN" and self.current().type != "EOF":
                self.advance()
            if self.current().type == "RPAREN":
                self.advance()

        return params
    
    def _parse_simple_value(self):
        """Parsii yksinkertaisen arvon (oletusarvoja varten)"""
        if self.current().type == "NUMBER":
            val = self.current().value
            self.advance()
            try:
                if '.' in val:
                    return float(val)
                else:
                    return int(val)
            except ValueError:
                return val
        elif self.current().type == "STRING":
            val = self.current().value
            self.advance()
            return val
        elif self.current().type == "IDENT":
            val = self.current().value
            self.advance()
            return val
        return None
    
    # ========== PARSE METODIT ==========
    
    def parseBlock(self) -> List[ASTNode]:
        nodes = []
        while self.current().type != "EOF":
            start_pos = self.pos
            node = self.parseStatement()
            if node:
                nodes.append(node)
            if self.pos == start_pos:
                self.advance()
        return nodes
    
    def parseStatement(self) -> Optional[ASTNode]:
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

        if tok.type == "IDENT" and tok.value.lower() == "print":
            return self.parsePrintStatement()

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
    
    def parseInclude(self) -> Optional[IncludeNode]:
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
        
        return IncludeNode(path)
    
    def parseTypeBlock(self) -> Optional[TypeNode]:
        if not self.match("IDENT", "type"):
            return None

        if self.current().type != "IDENT":
            return None

        type_name = self._normalize_identifier(self.current().value)
        self.advance()

        tnode = TypeNode(type_name)
        current_visibility = "public"

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

            handled, current_visibility = self._dispatch_type_block_line(current_visibility, tnode)
            if handled:
                pass
            else:
                self.advance()

        return tnode
    
    def _dispatch_type_block_line(self, visibility: str, tnode: TypeNode) -> Tuple[bool, str]:
        tok = self.current()
        key = tok.value.lower()
        
        if key in ("public", "private"):
            visibility = key
            self.advance()
            if self.current().type == "COLON":
                self.advance()
            return True, visibility
        
        if key == "dim":
            return self._handle_type_dim(visibility, tnode)
        
        handler_name = self.type_block_dispatch.get(key)
        if handler_name:
            handler = getattr(self, handler_name)
            result = handler(visibility, tnode)
            if result is None:
                return False, visibility
            return result
        
        return self._handle_type_field(visibility, tnode)
    
    def _handle_type_declare(self, visibility: str, tnode: TypeNode) -> Tuple[bool, str]:
        self.advance()  # ohita 'declare'

        # Tarkista onko constructor/destructor
        next_tok = self.current()
        if next_tok.value.lower() in ("constructor", "destructor"):
            return self.handleConstructorDestructor(visibility, tnode)

        kind = self.current().value.lower()  # 'sub' tai 'function'
        self.advance()

        name = self._normalize_identifier(self.current().value)
        self.advance()

        # KÄYTÄ YHTEISTÄ PARAMETRIPARSERIA
        params = self._parse_parameter_list()

        return_type = "Void"
        if kind == "function" and self.current().type == "IDENT" and self.current().value.lower() == "as":
            self.advance()
            if self.current().type == "IDENT":
                return_type = self._normalize_identifier(self.current().value)
                self.advance()

        normalized_visibility = self._normalize_identifier(visibility)
        new_method = MethodNode(name, params, return_type, normalized_visibility)

        existing_methods = [m for m in tnode.methods if isinstance(m, MethodNode) and m.name == name]
        if not existing_methods:
            tnode.methods.append(new_method)

        return True, visibility
    
    def _handle_type_static(self, visibility: str, tnode: TypeNode) -> Tuple[bool, str]:
        self.advance()

        if self.current().type != "IDENT":
            return False, visibility

        field_name = self._normalize_identifier(self.current().value)
        self.advance()

        if self.current().type != "IDENT" or self.current().value.lower() != "as":
            return False, visibility
        self.advance()

        if self.current().type != "IDENT":
            return False, visibility

        type_name = self._normalize_identifier(self.current().value)
        self.advance()

        normalized_visibility = self._normalize_identifier(visibility)
        fnode = FieldNode(field_name, type_name, normalized_visibility, is_static=True)
        tnode.fields.append(fnode)

        return True, visibility
    
    def _handle_type_dim(self, visibility: str, tnode: TypeNode) -> Tuple[bool, str]:
        self.advance()

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

            name = self._normalize_identifier(self.current().value)
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
            type_name = self._normalize_identifier(self.current().value)
            self.advance()

            normalized_visibility = self._normalize_identifier(visibility)
            fnode = FieldNode(name, type_name, normalized_visibility, is_static=is_static)
            tnode.fields.append(fnode)

            if self.current().type == "COMMA":
                self.advance()
                continue

            return True, visibility
    
    def _handle_type_property(self, visibility: str, tnode: TypeNode) -> Tuple[bool, str]:
        self.advance()

        if self.current().type != "IDENT":
            return False, visibility

        name = self._normalize_identifier(self.current().value)
        self.advance()

        if self.current().type != "IDENT" or self.current().value.lower() != "as":
            return False, visibility
        self.advance()

        if self.current().type != "IDENT":
            return False, visibility

        type_name = self._normalize_identifier(self.current().value)
        self.advance()

        normalized_visibility = self._normalize_identifier(visibility)
        prop_node = PropertyNode(name, type_name, normalized_visibility, [], [])
        tnode.properties.append(prop_node)

        while self.current().type != "EOF":
            if self.current().type == "IDENT" and self.current().value.lower() == "end":
                nxt = self.peek()
                if nxt.type == "IDENT" and nxt.value.lower() == "property":
                    self.advance()
                    self.advance()
                    break
            self.advance()

        return True, visibility
    
    def handleConstructorDestructor(self, visibility: str, tnode: TypeNode) -> Tuple[bool, str]:
        kind_tok = self.current()
        kind = kind_tok.value.lower()
        self.advance()

        type_name = tnode.name

        # KÄYTÄ YHTEISTÄ PARAMETRIPARSERIA
        params = self._parse_parameter_list()

        normalized_visibility = self._normalize_identifier(visibility)
        ctor_dtor = ConstructorDestructorNode(kind, type_name, normalized_visibility, [])
        ctor_dtor.params = params

        existing_ctors_dtors = [
            m for m in tnode.methods 
            if isinstance(m, ConstructorDestructorNode) and m.kind == kind
        ]

        existing_methods = [
            m for m in tnode.methods 
            if isinstance(m, MethodNode) and 
            ((kind == "constructor" and m.is_constructor) or 
             (kind == "destructor" and m.is_destructor))
        ]

        if not existing_ctors_dtors and not existing_methods:
            tnode.methods.append(ctor_dtor)

        return True, visibility
    
    def _handle_type_field(self, visibility: str, tnode: TypeNode) -> Tuple[bool, str]:
        if self.current().type != "IDENT":
            return False, visibility
        name = self._normalize_identifier(self.current().value)
        self.advance()

        if self.current().type == "LPAREN":
            while self.current().type not in ("RPAREN", "EOF"):
                self.advance()
            if self.current().type == "RPAREN":
                self.advance()

        if self.current().type != "IDENT" or self.current().value.lower() != "as":
            return False, visibility
        self.advance()

        if self.current().type != "IDENT":
            return False, visibility
        type_name = self._normalize_identifier(self.current().value)
        self.advance()

        normalized_visibility = self._normalize_identifier(visibility)
        fnode = FieldNode(name, type_name, normalized_visibility, is_static=False)
        tnode.fields.append(fnode)

        return True, visibility
    
    def _handle_visibility(self, visibility: str, tnode: TypeNode) -> Tuple[bool, str]:
        new_vis = self._normalize_identifier(self.current().value.lower())
        self.advance()
        if self.current().type == "COLON":
            self.advance()
        return True, new_vis
    
    def parseDim(self) -> Optional[DimNode]:
        start_pos = self.pos

        # DEBUG-tulostus
        # print(f"DEBUG parseDim: current token = {self.current().type} '{self.current().value}'")

        # Tarkista onko DIM
        if not (self.current().type == "IDENT" and self.current().value.lower() == "dim"):
            # Ei ole DIM, tarkista onko SHARED (ilman DIM:ää)
            if not (self.current().type == "IDENT" and self.current().value.lower() == "shared"):
                return None
            else:
                # On SHARED ilman DIM:ää
                self.advance()  # Siirry SHARED:n yli
                is_shared = True
                is_dim = False
        else:
            # On DIM
            self.advance()  # Siirry DIM:n yli
            is_dim = True
            is_shared = False

        # Jos oli DIM, tarkista onko sen jälkeen SHARED
        if is_dim and self.current().type == "IDENT" and self.current().value.lower() == "shared":
            is_shared = True
            self.advance()

        is_static = False
        # Tarkista STATIC (vain DIM:n jälkeen)
        if is_dim and self.current().type == "IDENT" and self.current().value.lower() == "static":
            is_static = True
            self.advance()

        # DEBUG
        # print(f"DEBUG: is_dim={is_dim}, is_shared={is_shared}, is_static={is_static}")

        decls = []
        while True:
            if self.current().type != "IDENT":
                if decls:
                    break
                self.pos = start_pos
                return None

            name = self._normalize_identifier(self.current().value)
            self.advance()

            dims = None
            if self.current().type == "LPAREN":
                dims = self._parseArrayDimensions()

            if not self.match("IDENT", "as"):
                self.pos = start_pos
                return None

            if self.current().type != "IDENT":
                self.pos = start_pos
                return None
            type_name = self._normalize_identifier(self.current().value)
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

            if self.current().type != "COMMA":
                break
            self.advance()

        # DEBUG
        # print(f"DEBUG: Created DimNode with {len(decls)} declarations: {decls}")

        return DimNode(decls)
    
    def _parseArrayDimensions(self) -> Optional[List[Tuple[str, str]]]:
        if not self.match("LPAREN"):
            return None
        
        dims = []
        while self.current().type != "RPAREN" and self.current().type != "EOF":
            lower = None
            upper = None
            if self.current().type in ("NUMBER", "IDENT"):
                lower = self.current().value
                self.advance()
                if self.match("IDENT", "to"):
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
        
        if self.match("RPAREN"):
            pass
        
        return dims
    
    def _parseInitializer(self) -> Optional[Dict[str, Any]]:
        if self.current().type == "STRING":
            value = self.current().value
            self.advance()
            return {"type": "string", "value": value}
        elif self.current().type == "NUMBER":
            value = self.current().value
            self.advance()
            return {"type": "number", "value": value}
        elif self.current().type == "IDENT":
            # NORMALISOI CONSTRUCTOR-NIMI
            value = self._normalize_identifier(self.current().value)
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
    
    def parseAssignment(self) -> Optional[AssignmentNode]:
        tok = self.current()

        if tok.type == "IDENT" and tok.value.lower() == "print":
            return None

        if tok.type != "IDENT":
            return None

        start_line = tok.line
        left_tokens = []
        left_tokens.append(tok.value)
        self.advance()

        while True:
            tok = self.current()
            if tok.type in ("DOT", "LPAREN"):
                left_tokens.append(tok.value)
                self.advance()
            elif tok.type in ("NUMBER", "IDENT", "RPAREN", "COMMA"):
                left_tokens.append(tok.value)
                self.advance()
            elif tok.type == "COLON":
                return None
            else:
                break

        tok = self.current()
        if tok.type != "EQUAL":
            return None
        self.advance()

        right_tokens = []
        while (self.current().type != "EOF" and 
               self.current().line == start_line):
            if self.current().type == "COLON":
                break

            if self.current().type == "IDENT":
                next_val = self.current().value.lower()
                if (next_val in ["dim", "type", "print", "sub", "function", 
                                 "end", "constructor", "destructor", "declare"] or
                    next_val in self.statement_dispatch):
                    break

            right_tokens.append(self.current().value)
            self.advance()

        if not right_tokens:
            return None

        left_repr = "".join(str(x) for x in left_tokens)
        right_repr = " ".join(str(x) for x in right_tokens)

        return AssignmentNode(left_repr, right_repr)
    
    def parseMethodImplementation(self) -> Optional[MethodNode]:
        tok = self.current()

        if tok.type != "IDENT" or tok.value.lower() not in ("function", "sub", "constructor", "destructor"):
            return None

        kind = tok.value.lower()
        self.advance()

        if self.current().type != "IDENT":
            return None

        name = self._normalize_identifier(self.current().value)
        self.advance()

        # KÄYTÄ YHTEISTÄ PARAMETRIPARSERIA
        params = self._parse_parameter_list()

        return_type = None
        if kind == "function":
            if self.match("IDENT", "as"):
                if self.current().type == "IDENT":
                    return_type = self._normalize_identifier(self.current().value)
                    self.advance()

        # Ohita runko
        while True:
            tok = self.current()
            if tok.type == "IDENT" and tok.value.lower() == "end":
                nxt = self.peek()
                if nxt.type == "IDENT" and nxt.value.lower() == kind:
                    self.advance()
                    self.advance()
                    break
            self.advance()

        if kind in ("constructor", "destructor"):
            # Luo MethodNode constructorille/destructorille
            method_node = MethodNode(name, params, return_type or "Void", "public")
            method_node.is_constructor = (kind == "constructor")
            method_node.is_destructor = (kind == "destructor")
            return method_node
        else:
            return MethodNode(name, params, return_type or "Void", "public")
    
    def parseGlobalDeclare(self) -> Optional[GlobalDeclareNode]:
        if not self.match("IDENT", "declare"):
            return None

        tok = self.current()
        if tok.type != "IDENT" or tok.value.lower() not in ("function", "sub"):
            return None

        kind = tok.value.lower()
        self.advance()

        if self.current().type != "IDENT":
            return None

        name = self._normalize_identifier(self.current().value)
        self.advance()

        # KÄYTÄ YHTEISTÄ PARAMETRIPARSERIA
        params = self._parse_parameter_list()

        return_type = None
        if kind == "function":
            if self.match("IDENT", "as"):
                if self.current().type == "IDENT":
                    return_type = self._normalize_identifier(self.current().value)
                    self.advance()

        return GlobalDeclareNode(kind, name, params, return_type)
    
    def parsePrintStatement(self) -> Optional[ASTNode]:
        if not self.match("IDENT", "print"):
            return None

        values = []
        while (self.current().type != "EOF" and 
               self.current().type != "IDENT" and 
               self.current().value.lower() not in ["end", "sub", "function", "constructor", "destructor"]):
            if self.current().value.lower() in self.statement_dispatch:
                break

            values.append(self.current().value)
            self.advance()

        printed_value = " ".join(values).strip()
        if printed_value.endswith(','):
            printed_value = printed_value[:-1].strip()

        return AssignmentNode("PRINT", printed_value)
    def _normalize_identifier(self, ident: str) -> str:
        """Normalisoi kaikki FreeBASIC-identifikaattorit pieniksi kirjaimiksi"""
        if ident is None:
            return ""
        return ident.lower()


# ==================== APUFUNKTIOT ====================

def tokenize_source(source: str, filename: str = "") -> Tokenizer:
    """Tokenisoi lähdekoodin"""
    t = Tokenizer(source, filename)
    t._tokenize()
    return t


def parse_source(source: str, filename: str = "") -> Tuple[ProgramNode, SymbolTable]:
    """Pääfunktio parsinta varten"""
    tokenizer = tokenize_source(source, filename)
    parser = Parser(tokenizer.get_tokens(), base_path=os.path.dirname(filename) if filename else "")
    
    statements = parser.parseBlock()
    ast = ProgramNode(statements)
    
    collector = SymbolCollectorVisitor()
    ast.accept(collector)
    
    return ast, collector.symbol_table


# ==================== ESIMERKKI KÄYTTÖ ====================

if __name__ == "__main__":

    import sys
    import io
    import pyperclip


    # Lisää testi parserin loppuun
    #test_simple = "Dim Shared counter As Integer"
    #tokens = tokenize_source(test_simple).get_tokens()
    #parser = Parser(tokens)
    #result = parser.parseDim()
    #print(f"Test: '{test_simple}'")
    #print(f"Result: {result}")
    #if result:
    #    print(f"Declarations: {result.decls}")

    #sys.exit()




    # Testi FreeBASIC-koodi
    test_code = '''
    Type Person
        Name As String
        Age As Integer
        
        Declare Constructor()
        Declare Destructor()
        
        Private:
            ID As Integer
    End Type
    
    Dim x As Integer
    Dim y As Person
    Dim z As String = "Hello"
    
    x = 42
    '''
    
    # --- Aloitetaan tulostuksen sieppaus ---
    buffer = io.StringIO()
    sys.stdout = buffer

    file = "dim.bas"
    filepath = "Freebasic_statements"
    testitiedosto = os.path.join(os.path.dirname(__file__), filepath, file)
    with open(testitiedosto, "r", encoding="utf-8", errors="ignore") as f:
            test_code = f.read()

    # Parse ja kerää symbolit
    ast, symbols = parse_source(test_code, testitiedosto)
    
    print("=== AST TYYPIT ===")
    for stmt in ast.statements:
        print(f"- {stmt.kind}: {getattr(stmt, 'name', 'N/A')}")
    
    print("\n=== SYMBOLIT ===")
    print(f"Tyypit: {list(symbols.types.keys())}")
    print(f"Muuttujat: {list(symbols.variables.keys())}")
    
    print("\n=== TYYPPIEN TIEDOT ===")
    for name, ts in symbols.types.items():
        print(str(ts))
    
    print("\n=== LSP-TIEDOT ===")
    print("Types dict:", symbols.all_types_dict())
    print("\nVars dict:", symbols.var_to_type_dict())
    
    print("\n=== VISITOR DEMO ===")
    # Voit luoda muita visitoreita helposti!
    class DebugVisitor(BaseVisitor):
        def visit_ProgramNode(self, node):
            print(f"Debug: Found Program with {len(node.statements)} statements")
            self.generic_visit(node)

        def visit_TypeNode(self, node):
            print(f"Debug: Found type {node.name} with {len(node.fields)} fields")
            self.generic_visit(node)

        def visit_FieldNode(self, node):
            print(f"Debug: Found field {node.name} of type {node.type_name}")

        def visit_MethodNode(self, node):
            print(f"Debug: Found method {node.name}")

        def visit_DimNode(self, node):
            print(f"Debug: Found DIM with {len(node.decls)} declarations")

        def visit_AssignmentNode(self, node):
            print(f"Debug: Found assignment {node.target} = {node.value}")

        def visit_IncludeNode(self, node):
            print(f"Debug: Found include {node.path}")

        def visit_StaticFieldNode(self, node):
            print(f"Debug: Found static field {node.name}")

        def visit_VarDeclNode(self, node):
            print(f"Debug: Found var declaration {node.name} As {node.type_name}")

        def visit_GlobalDeclareNode(self, node):
            print(f"Debug: Found global declare {node.kind} {node.name}")

        def visit_ConstructorDestructorNode(self, node):
            print(f"Debug: Found {node.kind} for type {node.name}")

        def visit_PropertyNode(self, node):
            print(f"Debug: Found property {node.name}")
    
    debugger = DebugVisitor()
    ast.accept(debugger)

    # --- Lopetetaan tulostuksen sieppaus ---
    sys.stdout = sys.__stdout__
    # Kopioidaan leikepöydälle
    pyperclip.copy(buffer.getvalue())
    # Näytetään tulostus myös terminaalissa
    print(buffer.getvalue())
    print("\033[1m\033[32m📋 Teksti on leikepöydällä\033[0m")
