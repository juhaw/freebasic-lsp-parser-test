# ===========================
# Refaktoroitu parseDim + parseType
# ===========================

def parseDim(self):
    """Pääfunktio DIM-lauseelle."""
    self.expect("KEYWORD", "dim")
    shared = False
    if self.match("KEYWORD", "shared"):
        shared = True

    # Valitse DBNF:n mukainen polku
    if self.match("KEYWORD", "as"):
        type_name, variables = self.parseDimAsType()
    else:
        variables, type_name = self.parseDimNamesThenType()

    # Arrayt ja initializer
    array_bounds = []
    initializer = None
    for i, var in enumerate(variables):
        bounds, init = self.parseDimVarExtras()
        array_bounds.append(bounds)
        if i == 0:  # vain ensimmäinen muuttuja saa initializer nykyisessä FB
            initializer = init

        # Lisää symbolitauluun
        self.symbol_table.addVariable(VariableSymbol(var, type_name))

    node = DimNode(variables, type_name)
    node.array_bounds = array_bounds
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
    """DIM var1, var2 ... AS TypeName"""
    variables = []
    type_name = None

    # Kerää nimet
    while True:
        tok = self.current()
        if tok.type != "IDENT":
            break
        var_name = tok.value
        # suffix
        suffix_map = {'$': 'String', '%': 'Integer', '#': 'Double', '!': 'Single', '&': 'LongInt'}
        if var_name[-1:] in suffix_map:
            type_name = suffix_map[var_name[-1:]]
            var_name = var_name[:-1]
        variables.append(var_name)
        self.advance()
        if not self.match("COMMA"):
            break

    # As Type
    if self.match("KEYWORD", "as"):
        type_name = self.expect("IDENT").value

    return variables, type_name

def parseDimVarExtras(self):
    """Käsittelee array bounds ja initializer jokaiselle muuttujalle."""
    bounds = []
    initializer = None

    # Array spec
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


# ===========================
# Refaktoroitu parseType
# ===========================

def parseType(self):
    """Pääfunktio Type-lohkolle."""
    self.expect("KEYWORD", "Type")
    type_name_tok = self.expect("IDENT")
    tnode = TypeNode(name=type_name_tok.value, fields=[], methods=[])
    self.symbol_table.addType(TypeSymbol(tnode.name, [], []))

    current_visibility = "public"

    while True:
        tok = self.current()
        if tok.type == "KEYWORD":
            val = tok.value.lower()

            # Lopetus
            if val == "end" and self.peek().value.lower() == "type":
                self.advance()
                self.advance()
                break

            # Näkyvyys
            elif val in ("public", "private"):
                current_visibility = val
                self.advance()
                if self.current().type == "KEYWORD" and self.current().value == ":":
                    self.advance()
                continue

            # Static kenttä
            elif val == "static":
                fnode = self.parseStaticField(current_visibility)
                tnode.fields.append(fnode)
                continue

            # DIM kenttä
            elif val == "dim":
                dim_node = self.parseDim()
                for n, t in zip(dim_node.names, [dim_node.type_name]*len(dim_node.names)):
                    fnode = FieldNode(n, t, current_visibility)
                    tnode.fields.append(fnode)
                continue

        # Plain kenttä: IDENT AS IDENT
        if tok.type == "IDENT":
            fnode = self.parsePlainField(current_visibility)
            tnode.fields.append(fnode)
            continue

        # Declare Method
        if tok.type == "KEYWORD" and tok.value.lower() == "declare":
            mnode = self.parseTypeMethod(current_visibility)
            if mnode:
                tnode.methods.append(mnode)
            continue

        self.advance()

    return tnode

def parsePlainField(self, visibility="public"):
    """Käsittelee tavallisen kentän IDENT AS IDENT"""
    name_tok = self.expect("IDENT")
    self.expect("KEYWORD", "as")
    type_tok = self.expect("IDENT")
    return FieldNode(name_tok.value, type_tok.value, visibility)
