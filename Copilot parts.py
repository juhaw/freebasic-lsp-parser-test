def parseType(self):
    """Parser for TYPE blocks in FreeBASIC, dictionary-based, AI slot-ready."""
    self.expect_keyword("type")
    name_tok = self.expect_ident()

    # === AI_INSERT_POINT:TYPE_BODY ===
    # AI voi liittää handler-funktiot ja lisälogiikan tähän
    # </AI_INSERT_POINT>

    fields = []
    methods = []
    current_visibility = "public"

    # Helper-funktio näkyvyyden asettamiseen
    def setVisibility(vis):
        nonlocal current_visibility
        current_visibility = vis
        return None  # Ei AST-solmua luoda

    # Dictionary, joka ohjaa avainsanat oikeaan käsittelyyn
    type_keyword_handlers = {
        "public": lambda: setVisibility("public"),
        "private": lambda: setVisibility("private"),
        "declare": lambda: self.parseDeclareField(current_visibility),
        "static": lambda: self.parseStaticField(current_visibility),
        "method": lambda: self.parseTypeMethod(current_visibility),
        "operator": lambda: self.parseTypeOperator(current_visibility),
        # Lisää uusia avainsanoja tarvittaessa
    }

    # Kerätään tokenit TYPE-body:stä
    tokens_in_type_body = self.collectTypeTokens()

    for tok in tokens_in_type_body:
        v = tok.value.lower() if tok.type == "KEYWORD" else "ident"

        handler = type_keyword_handlers.get(v)
        if handler:
            node = handler()
            if node:
                if isinstance(node, MethodNode):
                    methods.append(node)
                elif isinstance(node, FieldNode):
                    fields.append(node)
            continue

        # Jos tunnistamaton ident → oletetaan kenttä
        if tok.type == "IDENT":
            node = self.parseTypeField(current_visibility)
            if node:
                fields.append(node)
            continue

        self.advance()

    self.expect_keyword("end")
    self.expect_keyword("type")

    # Luo AST-solmu
    type_node = TypeNode(name_tok.value, fields, methods)

    # Päivitä symbolitaulu ja staattiset kentät
    type_symbol = TypeSymbol(type_node.name, type_node.fields, type_node.methods)
    for f in type_node.fields:
        if getattr(f, "is_static", False):
            type_symbol.static_fields.append(f)
    self.symbol_table.addType(type_symbol)

    return type_node
