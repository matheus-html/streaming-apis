from lxml import etree

from core import servicos
from core.erros import Conflito, Invalido, NaoEncontrado

from .contrato import NS, OPERACOES, RECURSOS, TIPOS

ENV = "http://schemas.xmlsoap.org/soap/envelope/"
PARSER = etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=False)


def _qualificado(nome):
    return f"{{{NS}}}{nome}"


def _nome_local(elemento):
    return etree.QName(elemento).localname


def _filho(pai, nome):
    for filho in pai:
        if isinstance(filho.tag, str) and _nome_local(filho) == nome:
            return filho
    return None


def _inteiro(texto, nome):
    try:
        return int((texto or "").strip())
    except ValueError:
        raise Invalido(f"campo '{nome}' deve ser um inteiro") from None


def ler(elemento, tipo, nome):
    base = tipo.rstrip("?")
    if base == "texto":
        return elemento.text or ""
    if base in ("inteiro", "longo"):
        return _inteiro(elemento.text, nome)
    if base == "booleano":
        valor = (elemento.text or "").strip().lower()
        if valor not in ("true", "false", "1", "0"):
            raise Invalido(f"campo '{nome}' deve ser booleano")
        return valor in ("true", "1")
    if base == "decimal":
        try:
            return float((elemento.text or "").strip())
        except ValueError:
            raise Invalido(f"campo '{nome}' deve ser numérico") from None
    if base == "lista_texto":
        return [filho.text or "" for filho in elemento]
    if base == "lista_int":
        return [_inteiro(filho.text, nome) for filho in elemento]
    if base.startswith("obj:"):
        return ler_objeto(elemento, base[4:])
    if base.startswith("lista:"):
        return [ler_objeto(filho, base[6:]) for filho in elemento]
    raise Invalido(f"tipo desconhecido para '{nome}'")


def ler_objeto(elemento, tipo):
    dados = {}
    for campo, tipo_campo in TIPOS[tipo]:
        filho = _filho(elemento, campo)
        if filho is not None:
            dados[campo] = ler(filho, tipo_campo, campo)
    return dados


def texto(valor):
    if isinstance(valor, bool):
        return "true" if valor else "false"
    return str(valor)


def escrever(pai, nome, valor, tipo):
    if valor is None:
        return
    elemento = etree.SubElement(pai, _qualificado(nome))
    base = tipo.rstrip("?")
    if base in ("lista_texto", "lista_int"):
        for item in valor:
            etree.SubElement(elemento, _qualificado("item")).text = texto(item)
    elif base.startswith("obj:"):
        escrever_campos(elemento, valor, base[4:])
    elif base.startswith("lista:"):
        for item in valor:
            filho = etree.SubElement(elemento, _qualificado("item"))
            escrever_campos(filho, item, base[6:])
    else:
        elemento.text = texto(valor)


def escrever_campos(elemento, dados, tipo):
    for campo, tipo_campo in TIPOS[tipo]:
        if campo in dados:
            escrever(elemento, campo, dados[campo], tipo_campo)


def envelope(corpo):
    raiz = etree.Element(f"{{{ENV}}}Envelope", nsmap={"soap": ENV, "tns": NS})
    etree.SubElement(raiz, f"{{{ENV}}}Body").append(corpo)
    return etree.tostring(raiz, xml_declaration=True, encoding="utf-8")


def falha(codigo, mensagem):
    erro = etree.Element(f"{{{ENV}}}Fault")
    etree.SubElement(erro, "faultcode").text = "soap:Client"
    etree.SubElement(erro, "faultstring").text = mensagem
    detalhe = etree.SubElement(erro, "detail")
    etree.SubElement(detalhe, _qualificado("codigo")).text = codigo
    return envelope(erro)


def argumentos(requisicao, operacao):
    campos, _ = OPERACOES[operacao]
    valores = {}
    for nome, tipo in campos:
        filho = _filho(requisicao, nome)
        if filho is None:
            if not tipo.endswith("?"):
                raise Invalido(f"campo '{nome}' é obrigatório")
            valores[nome] = None
        else:
            valores[nome] = ler(filho, tipo, nome)
    return valores


def montar_resposta(operacao, resultado):
    _, resposta = OPERACOES[operacao]
    raiz = etree.Element(_qualificado(f"{operacao}Response"), nsmap={"tns": NS})
    if resposta[0] == "entidade":
        escrever(raiz, resposta[1], resultado, "obj:" + resposta[2])
    elif resposta[0] == "pagina":
        for item in resultado["itens"]:
            escrever(raiz, resposta[1], item, "obj:" + resposta[2])
        escrever(raiz, "pagina", resultado["pagina"], "inteiro")
        escrever(raiz, "tamanho", resultado["tamanho"], "inteiro")
        escrever(raiz, "total", resultado["total"], "longo")
    return raiz


def tratadores():
    mapa = {}
    for tipo, plural, nome in RECURSOS:
        recurso = getattr(servicos, plural.lower())
        mapa[f"Listar{plural}"] = lambda a, r=recurso: r.listar(a["pagina"], a["tamanho"], a["nome"])
        mapa[f"Obter{tipo}"] = lambda a, r=recurso: r.obter(a["id"])
        mapa[f"Criar{tipo}"] = lambda a, r=recurso, n=nome: r.criar(a[n])
        mapa[f"Atualizar{tipo}"] = lambda a, r=recurso, n=nome: r.atualizar(a["id"], a[n])
        mapa[f"Remover{tipo}"] = lambda a, r=recurso: r.remover(a["id"])
    mapa["ListarPlaylistsDoUsuario"] = lambda a: servicos.playlists_do_usuario(a["id"], a["pagina"], a["tamanho"])
    mapa["ListarMusicasDaPlaylist"] = lambda a: servicos.musicas_da_playlist(a["id"], a["pagina"], a["tamanho"])
    mapa["ListarPlaylistsDaMusica"] = lambda a: servicos.playlists_da_musica(a["id"], a["pagina"], a["tamanho"])
    return mapa


TRATADORES = tratadores()


def processar(corpo):
    try:
        try:
            raiz = etree.fromstring(corpo, PARSER)
        except etree.XMLSyntaxError:
            raise Invalido("XML malformado") from None
        if _nome_local(raiz) != "Envelope":
            raise Invalido("o elemento raiz deve ser Envelope")
        conteudo = _filho(raiz, "Body")
        requisicao = next((f for f in conteudo if isinstance(f.tag, str)), None) if conteudo is not None else None
        if requisicao is None:
            raise Invalido("Body vazio")
        operacao = _nome_local(requisicao)
        if operacao not in TRATADORES:
            raise Invalido(f"operação desconhecida: {operacao}")
        resultado = TRATADORES[operacao](argumentos(requisicao, operacao))
        return 200, envelope(montar_resposta(operacao, resultado))
    except NaoEncontrado as erro:
        return 500, falha("NAO_ENCONTRADO", str(erro))
    except Invalido as erro:
        return 500, falha("ENTRADA_INVALIDA", str(erro))
    except Conflito as erro:
        return 500, falha("CONFLITO", str(erro))