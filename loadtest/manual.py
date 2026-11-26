from crud_comum import dados_musica, dados_playlist, dados_usuario, musicas_sorteadas
from graphql_consultas import MUSICA, PLAYLIST, USUARIO

import argparse
import json
import sys
import time
import xml.etree.ElementTree as ET

import requests

RECURSOS = {
    "usuario": {
        "rotulo": "Usuários", "um": "usuário", "caminho": "/usuarios", "classe": "Usuario",
        "plural": "Usuarios", "gql_lista": "usuarios", "campos": USUARIO,
    },
    "musica": {
        "rotulo": "Músicas", "um": "música", "caminho": "/musicas", "classe": "Musica",
        "plural": "Musicas", "gql_lista": "musicas", "campos": MUSICA,
    },
    "playlist": {
        "rotulo": "Playlists", "um": "playlist", "caminho": "/playlists", "classe": "Playlist",
        "plural": "Playlists", "gql_lista": "playlists", "campos": PLAYLIST,
    },
}
RELACIONADOS = {
    "usuario": ("playlists_do_usuario", "Playlists do usuário", "playlist"),
    "musica": ("playlists_da_musica", "Playlists que contêm a música", "playlist"),
    "playlist": ("musicas_da_playlist", "Músicas da playlist", "musica"),
}
REST_RELACIONADOS = {
    "playlists_do_usuario": "/usuarios/{}/playlists",
    "musicas_da_playlist": "/playlists/{}/musicas",
    "playlists_da_musica": "/musicas/{}/playlists",
}
SOAP_RELACIONADOS = {
    "playlists_do_usuario": "ListarPlaylistsDoUsuario",
    "musicas_da_playlist": "ListarMusicasDaPlaylist",
    "playlists_da_musica": "ListarPlaylistsDaMusica",
}
GRAPHQL_RELACIONADOS = {
    "playlists_do_usuario": ("playlistsDoUsuario", "usuarioId"),
    "musicas_da_playlist": ("musicasDaPlaylist", "playlistId"),
    "playlists_da_musica": ("playlistsDaMusica", "musicaId"),
}
GRPC_RELACIONADOS = {
    "playlists_do_usuario": ("usuario", "ListarPlaylists"),
    "musicas_da_playlist": ("playlist", "ListarMusicas"),
    "playlists_da_musica": ("musica", "ListarPlaylists"),
}
INTEIROS_LONGOS = {"total", "totalMusicas", "duracaoTotalMs"}
TEMPO_LIMITE = 30
LIMITE_DETALHES = 4000


class Resultado:
    def __init__(self, ok, resumo, dados, detalhes, ms):
        self.ok = ok
        self.resumo = resumo
        self.dados = dados
        self.detalhes = detalhes
        self.ms = ms


def cronometro():
    return time.perf_counter()


def milissegundos(inicio):
    return (time.perf_counter() - inicio) * 1000


class ClienteRest:
    nome = "REST"

    def __init__(self, host):
        self.host = host.rstrip("/")
        self.sessao = requests.Session()

    def chamar(self, metodo, caminho, esperado, params=None, corpo=None):
        inicio = cronometro()
        resposta = self.sessao.request(
            metodo, self.host + caminho, params=params, json=corpo, timeout=TEMPO_LIMITE
        )
        ms = milissegundos(inicio)
        dados = None
        if resposta.text:
            try:
                dados = resposta.json()
            except ValueError:
                dados = resposta.text
        requisicao = f"{metodo} {resposta.request.url}"
        if corpo is not None:
            requisicao += "\n" + json.dumps(corpo, ensure_ascii=False, indent=2)
        detalhes = f"{requisicao}\n\n<- {resposta.status_code} {resposta.reason}\n{resposta.text}"
        resumo = f"{metodo} {caminho} -> {resposta.status_code}"
        return Resultado(resposta.status_code == esperado, resumo, dados, detalhes, ms)

    def listar(self, tipo, pagina, tamanho, nome):
        params = {k: v for k, v in (("pagina", pagina), ("tamanho", tamanho), ("nome", nome)) if v is not None}
        return self.chamar("GET", RECURSOS[tipo]["caminho"], 200, params=params)

    def obter(self, tipo, identificador):
        return self.chamar("GET", f"{RECURSOS[tipo]['caminho']}/{identificador}", 200)

    def criar(self, tipo, dados):
        return self.chamar("POST", RECURSOS[tipo]["caminho"], 201, corpo=dados)

    def atualizar(self, tipo, identificador, dados):
        return self.chamar("PUT", f"{RECURSOS[tipo]['caminho']}/{identificador}", 200, corpo=dados)

    def remover(self, tipo, identificador):
        return self.chamar("DELETE", f"{RECURSOS[tipo]['caminho']}/{identificador}", 204)

    def relacionados(self, chave, identificador, pagina, tamanho):
        params = {k: v for k, v in (("pagina", pagina), ("tamanho", tamanho)) if v is not None}
        return self.chamar("GET", REST_RELACIONADOS[chave].format(identificador), 200, params=params)


class ClienteGraphql:
    nome = "GraphQL"

    def __init__(self, host):
        from graphql_crud import atualizacao, criacao, obtencao, remocao

        self.host = host.rstrip("/")
        self.sessao = requests.Session()
        self.criacao = criacao
        self.atualizacao = atualizacao
        self.obtencao = obtencao
        self.remocao = remocao

    def executar(self, operacao, consulta, variaveis, chave):
        inicio = cronometro()
        resposta = self.sessao.post(
            self.host + "/graphql", json={"query": consulta, "variables": variaveis}, timeout=TEMPO_LIMITE
        )
        ms = milissegundos(inicio)
        try:
            corpo = resposta.json()
        except ValueError:
            corpo = {"errors": [{"message": resposta.text}]}
        erros = corpo.get("errors")
        ok = resposta.status_code == 200 and not erros
        dados = erros if erros else (corpo.get("data") or {}).get(chave)
        variaveis_texto = json.dumps(variaveis, ensure_ascii=False, indent=2)
        detalhes = (
            f"POST {self.host}/graphql\n{consulta}\nvariables: {variaveis_texto}\n\n"
            f"<- {resposta.status_code} {resposta.reason}\n{resposta.text}"
        )
        return Resultado(ok, f"POST /graphql ({operacao}) -> {resposta.status_code}", dados, detalhes, ms)

    def listar(self, tipo, pagina, tamanho, nome):
        r = RECURSOS[tipo]
        consulta = (
            "query($p: Int, $t: Int, $n: String) { %s(pagina: $p, tamanho: $t, nome: $n) "
            "{ itens { %s } pagina tamanho total } }" % (r["gql_lista"], r["campos"])
        )
        variaveis = {k: v for k, v in (("p", pagina), ("t", tamanho), ("n", nome)) if v is not None}
        return self.executar(f"{r['gql_lista']}", consulta, variaveis, r["gql_lista"])

    def obter(self, tipo, identificador):
        return self.executar(tipo, self.obtencao(tipo), {"id": identificador}, tipo)

    def criar(self, tipo, dados):
        return self.executar(
            f"criar{RECURSOS[tipo]['classe']}", self.criacao(tipo), {"e": dados}, f"criar{RECURSOS[tipo]['classe']}"
        )

    def atualizar(self, tipo, identificador, dados):
        nome = f"atualizar{RECURSOS[tipo]['classe']}"
        return self.executar(nome, self.atualizacao(tipo), {"id": identificador, "e": dados}, nome)

    def remover(self, tipo, identificador):
        nome = f"remover{RECURSOS[tipo]['classe']}"
        return self.executar(nome, self.remocao(tipo), {"id": identificador}, nome)

    def relacionados(self, chave, identificador, pagina, tamanho):
        campo, argumento = GRAPHQL_RELACIONADOS[chave]
        tipo_item = next(r[2] for r in RELACIONADOS.values() if r[0] == chave)
        consulta = (
            "query($id: Int!, $p: Int, $t: Int) { %s(%s: $id, pagina: $p, tamanho: $t) "
            "{ itens { %s } pagina tamanho total } }" % (campo, argumento, RECURSOS[tipo_item]["campos"])
        )
        variaveis = {"id": identificador}
        for k, v in (("p", pagina), ("t", tamanho)):
            if v is not None:
                variaveis[k] = v
        return self.executar(campo, consulta, variaveis, campo)


def sem_namespace(tag):
    return tag.rsplit("}", 1)[-1]


def converter_xml(no):
    filhos = list(no)
    if not filhos:
        return no.text or ""
    nomes = [sem_namespace(filho.tag) for filho in filhos]
    if all(nome == "item" for nome in nomes):
        return [converter_xml(filho) for filho in filhos]
    resultado = {}
    for filho, nome in zip(filhos, nomes):
        valor = converter_xml(filho)
        if nomes.count(nome) > 1:
            resultado.setdefault(nome, []).append(valor)
        else:
            resultado[nome] = valor
    return resultado


def interpretar_soap(conteudo):
    try:
        raiz = ET.fromstring(conteudo)
    except ET.ParseError:
        return None, {"erro": "resposta SOAP inválida"}
    corpo = next((filho for filho in raiz if sem_namespace(filho.tag) == "Body"), None)
    if corpo is None or len(corpo) == 0:
        return None, {"erro": "resposta SOAP sem corpo"}
    primeiro = corpo[0]
    if sem_namespace(primeiro.tag) == "Fault":
        return None, converter_xml(primeiro)
    return converter_xml(primeiro), None


class ClienteSoap:
    nome = "SOAP"

    def __init__(self, host):
        from soap_crud import CABECALHO, ENVELOPE, NS, elemento

        self.host = host.rstrip("/")
        self.sessao = requests.Session()
        self.cabecalho = CABECALHO
        self.envelope = ENVELOPE
        self.ns = NS
        self.elemento = elemento

    def chamar(self, operacao, corpo):
        envelope = self.envelope.format(operacao=operacao, corpo=corpo)
        cabecalho = {**self.cabecalho, "SOAPAction": f'"{self.ns}/{operacao}"'}
        inicio = cronometro()
        resposta = self.sessao.post(
            self.host + "/soap", data=envelope.encode("utf-8"), headers=cabecalho, timeout=TEMPO_LIMITE
        )
        ms = milissegundos(inicio)
        dados, falha = interpretar_soap(resposta.content)
        detalhes = (
            f"POST {self.host}/soap\nSOAPAction: {cabecalho['SOAPAction']}\n\n{envelope}\n\n"
            f"<- {resposta.status_code} {resposta.reason}\n{resposta.text}"
        )
        ok = resposta.status_code == 200 and falha is None
        return Resultado(
            ok, f"POST /soap ({operacao}) -> {resposta.status_code}", dados if ok else falha, detalhes, ms
        )

    def entidade(self, resultado, tipo):
        if resultado.ok and isinstance(resultado.dados, dict) and tipo in resultado.dados:
            resultado.dados = resultado.dados[tipo]
        return resultado

    def pagina(self, resultado, tipo):
        if resultado.ok and isinstance(resultado.dados, dict):
            itens = resultado.dados.get(tipo, [])
            if not isinstance(itens, list):
                itens = [itens]
            resultado.dados = {
                "itens": itens,
                "pagina": resultado.dados.get("pagina"),
                "tamanho": resultado.dados.get("tamanho"),
                "total": resultado.dados.get("total"),
            }
        return resultado

    def paginacao(self, pagina, tamanho):
        corpo = ""
        if pagina is not None:
            corpo += self.elemento("pagina", pagina)
        if tamanho is not None:
            corpo += self.elemento("tamanho", tamanho)
        return corpo

    def listar(self, tipo, pagina, tamanho, nome):
        corpo = self.paginacao(pagina, tamanho)
        if nome is not None:
            corpo += self.elemento("nome", nome)
        resultado = self.chamar(f"Listar{RECURSOS[tipo]['plural']}", corpo)
        return self.pagina(resultado, tipo)

    def obter(self, tipo, identificador):
        resultado = self.chamar(f"Obter{RECURSOS[tipo]['classe']}", self.elemento("id", identificador))
        return self.entidade(resultado, tipo)

    def criar(self, tipo, dados):
        resultado = self.chamar(f"Criar{RECURSOS[tipo]['classe']}", self.elemento(tipo, dados))
        return self.entidade(resultado, tipo)

    def atualizar(self, tipo, identificador, dados):
        corpo = self.elemento("id", identificador) + self.elemento(tipo, dados)
        resultado = self.chamar(f"Atualizar{RECURSOS[tipo]['classe']}", corpo)
        return self.entidade(resultado, tipo)

    def remover(self, tipo, identificador):
        return self.chamar(f"Remover{RECURSOS[tipo]['classe']}", self.elemento("id", identificador))

    def relacionados(self, chave, identificador, pagina, tamanho):
        tipo_item = next(r[2] for r in RELACIONADOS.values() if r[0] == chave)
        corpo = self.elemento("id", identificador) + self.paginacao(pagina, tamanho)
        resultado = self.chamar(SOAP_RELACIONADOS[chave], corpo)
        return self.pagina(resultado, tipo_item)


def normalizar_inteiros(valor):
    if isinstance(valor, dict):
        return {
            k: int(v) if k in INTEIROS_LONGOS and isinstance(v, str) and v.isdigit() else normalizar_inteiros(v)
            for k, v in valor.items()
        }
    if isinstance(valor, list):
        return [normalizar_inteiros(v) for v in valor]
    return valor


class ClienteGrpc:
    nome = "gRPC"

    def __init__(self, host):
        import grpc
        import grpc_crud
        from google.protobuf import json_format

        self.grpc = grpc
        self.crud = grpc_crud
        self.pb = grpc_crud.pb
        self.json_format = json_format
        self.alvo = host.split("://")[-1]
        canal = grpc.insecure_channel(self.alvo)
        pb_grpc = grpc_crud.base.pb_grpc
        self.servicos = {
            "usuario": pb_grpc.UsuarioServiceStub(canal),
            "musica": pb_grpc.MusicaServiceStub(canal),
            "playlist": pb_grpc.PlaylistServiceStub(canal),
        }

    def dicionario(self, mensagem):
        return self.json_format.MessageToDict(mensagem)

    def chamar(self, tipo, metodo, requisicao):
        rotulo = f"{RECURSOS[tipo]['classe']}Service/{metodo}"
        inicio = cronometro()
        try:
            resposta = getattr(self.servicos[tipo], metodo)(requisicao, timeout=TEMPO_LIMITE)
            ms = milissegundos(inicio)
            dados = normalizar_inteiros(self.dicionario(resposta))
            ok, status = True, "OK"
        except self.grpc.RpcError as erro:
            ms = milissegundos(inicio)
            dados = {"codigo": erro.code().name, "mensagem": erro.details()}
            ok, status = False, erro.code().name
        detalhes = (
            f"gRPC {self.alvo} {rotulo}\nrequisição:\n"
            f"{json.dumps(self.dicionario(requisicao), ensure_ascii=False, indent=2)}\n\n<- {status}\n"
            f"{json.dumps(dados, ensure_ascii=False, indent=2)}"
        )
        return Resultado(ok, f"{rotulo} -> {status}", dados, detalhes, ms)

    def listar(self, tipo, pagina, tamanho, nome):
        parametros = {k: v for k, v in (("pagina", pagina), ("tamanho", tamanho), ("nome", nome)) if v is not None}
        return self.chamar(tipo, "Listar", self.pb.ListarRequisicao(**parametros))

    def obter(self, tipo, identificador):
        return self.chamar(tipo, "Obter", self.pb.IdRequisicao(id=identificador))

    def criar(self, tipo, dados):
        return self.chamar(tipo, "Criar", self.crud.entrada(tipo, dados))

    def atualizar(self, tipo, identificador, dados):
        requisicao = self.crud.ATUALIZACOES[tipo](id=identificador, entrada=self.crud.entrada(tipo, dados))
        return self.chamar(tipo, "Atualizar", requisicao)

    def remover(self, tipo, identificador):
        return self.chamar(tipo, "Remover", self.pb.IdRequisicao(id=identificador))

    def relacionados(self, chave, identificador, pagina, tamanho):
        tipo, metodo = GRPC_RELACIONADOS[chave]
        parametros = {"id": identificador}
        for k, v in (("pagina", pagina), ("tamanho", tamanho)):
            if v is not None:
                parametros[k] = v
        return self.chamar(tipo, metodo, self.pb.ListarRelacionadosRequisicao(**parametros))


CLIENTES = {"rest": ClienteRest, "soap": ClienteSoap, "graphql": ClienteGraphql, "grpc": ClienteGrpc}


def ler(prompt, padrao=None):
    try:
        texto = input(prompt).strip()
    except EOFError:
        raise SystemExit(0)
    return texto if texto else padrao


def ler_inteiro(prompt, padrao=None):
    while True:
        texto = ler(prompt)
        if texto is None:
            return padrao
        try:
            return int(texto)
        except ValueError:
            print("Digite um número inteiro.")


def truncar(valor, limite=100):
    if isinstance(valor, str) and len(valor) > limite:
        return f"{valor[:limite]}… (+{len(valor) - limite} caracteres)"
    if isinstance(valor, list):
        itens = [truncar(item, limite) for item in valor[:8]]
        if len(valor) > 8:
            itens.append(f"… (+{len(valor) - 8} itens)")
        return itens
    if isinstance(valor, dict):
        return {chave: truncar(item, limite) for chave, item in valor.items()}
    return valor


def linha_item(tipo, item):
    identificador = str(item.get("id", "?")).rjust(6)
    if tipo == "usuario":
        return f"{identificador}  {item.get('nome')}  <{item.get('email')}>  plano={item.get('plano')}"
    if tipo == "musica":
        return f"{identificador}  {item.get('nome')} - {item.get('artista')}  ({item.get('anoLancamento')})"
    return (
        f"{identificador}  {item.get('nome')}  usuario={item.get('usuarioId')}  "
        f"faixas={item.get('totalMusicas')}"
    )


def mostrar(resultado, tipo_item, estado):
    marca = "OK" if resultado.ok else "ERRO"
    print(f"\n[{marca}] {resultado.resumo}  ({resultado.ms:.0f} ms)")
    if estado["detalhes"]:
        texto = resultado.detalhes
        if len(texto) > LIMITE_DETALHES:
            texto = f"{texto[:LIMITE_DETALHES]}\n… (+{len(texto) - LIMITE_DETALHES} caracteres)"
        print("-" * 60)
        print(texto)
        print("-" * 60)
    dados = resultado.dados
    if not resultado.ok:
        if dados not in (None, ""):
            print(json.dumps(truncar(dados), ensure_ascii=False, indent=2))
        return
    if isinstance(dados, dict) and "itens" in dados:
        print(f"Página {dados.get('pagina')}, tamanho {dados.get('tamanho')}, total {dados.get('total')}")
        for item in dados["itens"]:
            print(linha_item(tipo_item, item))
        if not dados["itens"]:
            print("(nenhum resultado)")
        return
    if dados in (None, "", True) or dados == {}:
        print("Operação concluída.")
        return
    print(json.dumps(truncar(dados), ensure_ascii=False, indent=2))


def campos_editaveis(tipo):
    if tipo == "usuario":
        modelo = dados_usuario()
    elif tipo == "musica":
        modelo = dados_musica()
    else:
        modelo = dados_playlist(1, [])
    return ", ".join(modelo.keys())


def aplicar_alteracoes(dados):
    print('Altere campos com campo=valor (ex.: nome=Maria ou tags=["rock","pop"]). Enter vazio para continuar.')
    while True:
        linha = ler("campo=valor> ", "")
        if not linha:
            return dados
        if "=" not in linha:
            print("Use o formato campo=valor.")
            continue
        campo, valor = linha.split("=", 1)
        try:
            dados[campo.strip()] = json.loads(valor)
        except ValueError:
            dados[campo.strip()] = valor.strip()


def montar_dados(tipo):
    if tipo == "usuario":
        base = dados_usuario()
    elif tipo == "musica":
        base = dados_musica()
    else:
        dono = ler_inteiro("ID do usuário dono da playlist [1]: ", 1)
        base = dados_playlist(dono, musicas_sorteadas(3))
    print("Dados de exemplo:")
    print(json.dumps(truncar(base), ensure_ascii=False, indent=2))
    return aplicar_alteracoes(base)


def paginacao():
    pagina = ler_inteiro("Página [1]: ", 1)
    tamanho = ler_inteiro("Tamanho da página [10]: ", 10)
    return pagina, tamanho


def executar_opcao(cliente, tipo, opcao, estado):
    recurso = RECURSOS[tipo]
    chave_relacionada, rotulo_relacionado, tipo_relacionado = RELACIONADOS[tipo]
    if opcao == "1":
        pagina, tamanho = paginacao()
        mostrar(cliente.listar(tipo, pagina, tamanho, None), tipo, estado)
    elif opcao == "2":
        nome = ler("Texto do nome: ")
        if nome is None:
            print("Informe um texto.")
            return
        pagina, tamanho = paginacao()
        mostrar(cliente.listar(tipo, pagina, tamanho, nome), tipo, estado)
    elif opcao == "3":
        identificador = ler_inteiro(f"ID do {recurso['um']}: ")
        if identificador is not None:
            mostrar(cliente.obter(tipo, identificador), tipo, estado)
    elif opcao == "4":
        mostrar(cliente.criar(tipo, montar_dados(tipo)), tipo, estado)
    elif opcao == "5":
        identificador = ler_inteiro(f"ID do {recurso['um']} a atualizar: ")
        if identificador is None:
            return
        print(f"Campos disponíveis: {campos_editaveis(tipo)}")
        dados = aplicar_alteracoes({})
        if not dados:
            print("Nenhuma alteração informada.")
            return
        mostrar(cliente.atualizar(tipo, identificador, dados), tipo, estado)
    elif opcao == "6":
        identificador = ler_inteiro(f"ID do {recurso['um']} a remover: ")
        if identificador is None:
            return
        if (ler(f"Remover {recurso['um']} {identificador}? (s/N): ", "n") or "n").lower() != "s":
            print("Cancelado.")
            return
        mostrar(cliente.remover(tipo, identificador), tipo, estado)
    elif opcao == "7":
        identificador = ler_inteiro("ID: ")
        if identificador is None:
            return
        pagina, tamanho = paginacao()
        mostrar(cliente.relacionados(chave_relacionada, identificador, pagina, tamanho), tipo_relacionado, estado)
    else:
        print("Opção inválida.")


def menu_recurso(cliente, tipo, estado):
    recurso = RECURSOS[tipo]
    rotulo_relacionado = RELACIONADOS[tipo][1]
    while True:
        print(f"\n== {recurso['rotulo']} ==")
        print("  1) Listar")
        print("  2) Buscar por nome")
        print("  3) Obter por ID")
        print("  4) Criar")
        print("  5) Atualizar")
        print("  6) Remover")
        print(f"  7) {rotulo_relacionado}")
        print(f"  d) Detalhes do protocolo: {'ligado' if estado['detalhes'] else 'desligado'}")
        print("  0) Voltar")
        opcao = (ler("Opção: ", "") or "").lower()
        if opcao == "0":
            return
        if opcao == "d":
            estado["detalhes"] = not estado["detalhes"]
            continue
        try:
            executar_opcao(cliente, tipo, opcao, estado)
        except requests.RequestException as erro:
            print(f"Falha de conexão: {erro}")


def principal():
    analisador = argparse.ArgumentParser()
    analisador.add_argument("--api", required=True, choices=list(CLIENTES))
    analisador.add_argument("--host", required=True)
    analisador.add_argument("--versao", default="")
    argumentos = analisador.parse_args()
    cliente = CLIENTES[argumentos.api](argumentos.host)
    estado = {"detalhes": False}
    titulo = argumentos.versao or cliente.nome
    print(f"Modo manual: {titulo} ({cliente.nome}) em {argumentos.host}")
    tipos = {"1": "usuario", "2": "musica", "3": "playlist"}
    while True:
        print("\nEscolha o recurso:")
        print("  1) Usuários")
        print("  2) Músicas")
        print("  3) Playlists")
        print(f"  d) Detalhes do protocolo: {'ligado' if estado['detalhes'] else 'desligado'}")
        print("  0) Sair")
        opcao = (ler("Opção: ", "") or "").lower()
        if opcao == "0":
            return 0
        if opcao == "d":
            estado["detalhes"] = not estado["detalhes"]
        elif opcao in tipos:
            menu_recurso(cliente, tipos[opcao], estado)
        else:
            print("Opção inválida.")


if __name__ == "__main__":
    try:
        sys.exit(principal())
    except KeyboardInterrupt:
        print("\nEncerrado.")
        sys.exit(0)