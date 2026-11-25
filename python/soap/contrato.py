NS = "urn:streaming"
ENDERECO_PADRAO = "http://localhost:8080/soap"

PREFERENCIAS = [
    ("notificacoes", "booleano"), ("qualidadeAudio", "texto"), ("conteudoExplicito", "booleano"),
    ("crossfadeSegundos", "inteiro"), ("modoOffline", "booleano"),
]
HISTORICO_ITEM = [
    ("musicaId", "inteiro"), ("iniciadaEm", "texto"), ("duracaoOuvidaMs", "inteiro"), ("dispositivo", "texto"),
]
AUDIO = [
    ("bpm", "inteiro"), ("tonalidade", "texto"), ("energia", "decimal"), ("dancabilidade", "decimal"),
    ("valencia", "decimal"), ("acustica", "decimal"),
]

TIPOS = {
    "Preferencias": PREFERENCIAS,
    "HistoricoItem": HISTORICO_ITEM,
    "Audio": AUDIO,
    "Usuario": [
        ("id", "inteiro"), ("nome", "texto"), ("idade", "inteiro"), ("email", "texto"),
        ("username", "texto"), ("pais", "texto"), ("cidade", "texto"), ("plano", "texto"),
        ("dataCadastro", "texto"), ("ultimoAcesso", "texto"), ("bio", "texto"), ("idioma", "texto"),
        ("tema", "texto"), ("generosFavoritos", "lista_texto"), ("avatarUrl", "texto"),
        ("preferencias", "obj:Preferencias"), ("historicoRecente", "lista:HistoricoItem"),
    ],
    "Musica": [
        ("id", "inteiro"), ("nome", "texto"), ("artista", "texto"), ("album", "texto"),
        ("anoLancamento", "inteiro"), ("numeroFaixa", "inteiro"), ("duracaoMs", "inteiro"),
        ("genero", "texto"), ("idioma", "texto"), ("explicita", "booleano"), ("isrc", "texto"),
        ("gravadora", "texto"), ("popularidade", "inteiro"), ("letra", "texto"),
        ("compositores", "lista_texto"), ("produtores", "lista_texto"), ("tags", "lista_texto"),
        ("audio", "obj:Audio"),
    ],
    "Playlist": [
        ("id", "inteiro"), ("nome", "texto"), ("usuarioId", "inteiro"), ("descricao", "texto"),
        ("publica", "booleano"), ("colaborativa", "booleano"), ("criadaEm", "texto"),
        ("atualizadaEm", "texto"), ("capaUrl", "texto"), ("tags", "lista_texto"),
        ("totalMusicas", "longo"), ("duracaoTotalMs", "longo"), ("musicaIds", "lista_int"),
    ],
}

RECURSOS = [
    ("Usuario", "Usuarios", "usuario"),
    ("Musica", "Musicas", "musica"),
    ("Playlist", "Playlists", "playlist"),
]

PAGINACAO = [("pagina", "inteiro?"), ("tamanho", "inteiro?")]


def operacoes():
    ops = {}
    for tipo, plural, nome in RECURSOS:
        ops[f"Listar{plural}"] = ([*PAGINACAO, ("nome", "texto?")], ("pagina", nome, tipo))
        ops[f"Obter{tipo}"] = ([("id", "inteiro")], ("entidade", nome, tipo))
        ops[f"Criar{tipo}"] = ([(nome, f"obj:{tipo}")], ("entidade", nome, tipo))
        ops[f"Atualizar{tipo}"] = ([("id", "inteiro"), (nome, f"obj:{tipo}")], ("entidade", nome, tipo))
        ops[f"Remover{tipo}"] = ([("id", "inteiro")], ("vazio",))
    ops["ListarPlaylistsDoUsuario"] = ([("id", "inteiro"), *PAGINACAO], ("pagina", "playlist", "Playlist"))
    ops["ListarMusicasDaPlaylist"] = ([("id", "inteiro"), *PAGINACAO], ("pagina", "musica", "Musica"))
    ops["ListarPlaylistsDaMusica"] = ([("id", "inteiro"), *PAGINACAO], ("pagina", "playlist", "Playlist"))
    return ops


OPERACOES = operacoes()

XSD = {
    "texto": "xs:string", "inteiro": "xs:int", "longo": "xs:long",
    "booleano": "xs:boolean", "decimal": "xs:double",
    "lista_texto": "tns:ListaTexto", "lista_int": "tns:ListaInteiros",
}


def tipo_xsd(tipo):
    base = tipo.rstrip("?")
    if base.startswith("obj:"):
        return "tns:" + base[4:]
    if base.startswith("lista:"):
        return "tns:Lista" + base[6:]
    return XSD[base]


def elemento_xsd(nome, tipo, recuo, opcional):
    minimo = ' minOccurs="0"' if opcional else ""
    return f'{recuo}<xs:element name="{nome}" type="{tipo_xsd(tipo)}"{minimo}/>'


def gerar_wsdl(endereco=ENDERECO_PADRAO):
    linhas = []
    adicionar = linhas.append
    adicionar('<?xml version="1.0" encoding="UTF-8"?>')
    adicionar(
        f'<wsdl:definitions name="Streaming" targetNamespace="{NS}" '
        'xmlns:wsdl="http://schemas.xmlsoap.org/wsdl/" '
        'xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/" '
        f'xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:tns="{NS}">'
    )
    adicionar("  <wsdl:types>")
    adicionar(f'    <xs:schema targetNamespace="{NS}" elementFormDefault="qualified">')
    adicionar('      <xs:complexType name="ListaTexto"><xs:sequence>'
              '<xs:element name="item" type="xs:string" minOccurs="0" maxOccurs="unbounded"/>'
              "</xs:sequence></xs:complexType>")
    adicionar('      <xs:complexType name="ListaInteiros"><xs:sequence>'
              '<xs:element name="item" type="xs:int" minOccurs="0" maxOccurs="unbounded"/>'
              "</xs:sequence></xs:complexType>")
    adicionar('      <xs:complexType name="ListaHistoricoItem"><xs:sequence>'
              '<xs:element name="item" type="tns:HistoricoItem" minOccurs="0" maxOccurs="unbounded"/>'
              "</xs:sequence></xs:complexType>")
    for nome, campos in TIPOS.items():
        adicionar(f'      <xs:complexType name="{nome}">')
        adicionar("        <xs:sequence>")
        for campo, tipo in campos:
            adicionar(elemento_xsd(campo, tipo, "          ", True))
        adicionar("        </xs:sequence>")
        adicionar("      </xs:complexType>")
    for operacao, (requisicao, resposta) in OPERACOES.items():
        adicionar(f'      <xs:element name="{operacao}"><xs:complexType><xs:sequence>')
        for campo, tipo in requisicao:
            adicionar(elemento_xsd(campo, tipo, "        ", tipo.endswith("?")))
        adicionar("      </xs:sequence></xs:complexType></xs:element>")
        adicionar(f'      <xs:element name="{operacao}Response"><xs:complexType><xs:sequence>')
        if resposta[0] == "entidade":
            adicionar(elemento_xsd(resposta[1], "obj:" + resposta[2], "        ", False))
        elif resposta[0] == "pagina":
            adicionar(f'        <xs:element name="{resposta[1]}" type="tns:{resposta[2]}" '
                      'minOccurs="0" maxOccurs="unbounded"/>')
            adicionar('        <xs:element name="pagina" type="xs:int"/>')
            adicionar('        <xs:element name="tamanho" type="xs:int"/>')
            adicionar('        <xs:element name="total" type="xs:long"/>')
        adicionar("      </xs:sequence></xs:complexType></xs:element>")
    adicionar("    </xs:schema>")
    adicionar("  </wsdl:types>")
    for operacao in OPERACOES:
        adicionar(f'  <wsdl:message name="{operacao}Entrada"><wsdl:part name="parameters" element="tns:{operacao}"/></wsdl:message>')
        adicionar(f'  <wsdl:message name="{operacao}Saida"><wsdl:part name="parameters" element="tns:{operacao}Response"/></wsdl:message>')
    adicionar('  <wsdl:portType name="StreamingPortType">')
    for operacao in OPERACOES:
        adicionar(f'    <wsdl:operation name="{operacao}">')
        adicionar(f'      <wsdl:input message="tns:{operacao}Entrada"/>')
        adicionar(f'      <wsdl:output message="tns:{operacao}Saida"/>')
        adicionar("    </wsdl:operation>")
    adicionar("  </wsdl:portType>")
    adicionar('  <wsdl:binding name="StreamingBinding" type="tns:StreamingPortType">')
    adicionar('    <soap:binding style="document" transport="http://schemas.xmlsoap.org/soap/http"/>')
    for operacao in OPERACOES:
        adicionar(f'    <wsdl:operation name="{operacao}">')
        adicionar(f'      <soap:operation soapAction="{NS}/{operacao}"/>')
        adicionar('      <wsdl:input><soap:body use="literal"/></wsdl:input>')
        adicionar('      <wsdl:output><soap:body use="literal"/></wsdl:output>')
        adicionar("    </wsdl:operation>")
    adicionar("  </wsdl:binding>")
    adicionar('  <wsdl:service name="StreamingService">')
    adicionar('    <wsdl:port name="StreamingPort" binding="tns:StreamingBinding">')
    adicionar(f'      <soap:address location="{endereco}"/>')
    adicionar("    </wsdl:port>")
    adicionar("  </wsdl:service>")
    adicionar("</wsdl:definitions>")
    return "\n".join(linhas) + "\n"