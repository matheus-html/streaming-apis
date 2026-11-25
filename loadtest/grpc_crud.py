import time

import grpc
from google.protobuf import json_format
from locust import User, constant

import grpc_consultas as base
from comum import TIMEOUT
from crud_comum import CicloBase

pb = base.pb

ENTRADAS = {"usuario": pb.UsuarioEntrada, "musica": pb.MusicaEntrada, "playlist": pb.PlaylistEntrada}
ATUALIZACOES = {"usuario": pb.UsuarioAtualizacao, "musica": pb.MusicaAtualizacao, "playlist": pb.PlaylistAtualizacao}
LISTAS = {
    "usuario": ("generosFavoritos",),
    "musica": ("compositores", "produtores", "tags"),
    "playlist": ("tags", "musicaIds"),
}


def entrada(tipo, dados):
    copia = dict(dados)
    for campo in LISTAS[tipo]:
        if campo in copia:
            copia[campo] = {"valores": copia[campo]}
    return json_format.ParseDict(copia, ENTRADAS[tipo]())


class CicloGrpc(CicloBase):
    def on_start(self):
        super().on_start()
        canal = base.obter_canal(self.user.host.split("://")[-1])
        self.servicos = {
            "usuario": base.pb_grpc.UsuarioServiceStub(canal),
            "musica": base.pb_grpc.MusicaServiceStub(canal),
            "playlist": base.pb_grpc.PlaylistServiceStub(canal),
        }

    def chamar(self, nome, metodo, requisicao):
        inicio = time.perf_counter()
        erro = None
        resposta = None
        try:
            resposta = metodo(requisicao, timeout=TIMEOUT)
        except grpc.RpcError as excecao:
            erro = excecao
        self.user.environment.events.request.fire(
            request_type="gRPC",
            name=nome,
            response_time=(time.perf_counter() - inicio) * 1000,
            response_length=0,
            exception=erro,
            context={},
        )
        return resposta

    def criar(self, tipo, dados):
        resposta = self.chamar(f"criar {tipo}", self.servicos[tipo].Criar, entrada(tipo, dados))
        return resposta.id if resposta is not None else None

    def obter(self, tipo, identificador):
        self.chamar(f"obter {tipo}", self.servicos[tipo].Obter, pb.IdRequisicao(id=identificador))

    def atualizar(self, tipo, identificador, dados):
        requisicao = ATUALIZACOES[tipo](id=identificador, entrada=entrada(tipo, dados))
        self.chamar(f"atualizar {tipo}", self.servicos[tipo].Atualizar, requisicao)

    def remover(self, tipo, identificador):
        self.chamar(f"remover {tipo}", self.servicos[tipo].Remover, pb.IdRequisicao(id=identificador))

    def relacionados(self, nome, identificador):
        requisicao = pb.ListarRelacionadosRequisicao(id=identificador)
        if nome == "playlists_do_usuario":
            self.chamar(nome, self.servicos["usuario"].ListarPlaylists, requisicao)
        elif nome == "musicas_da_playlist":
            self.chamar(nome, self.servicos["playlist"].ListarMusicas, requisicao)
        else:
            self.chamar(nome, self.servicos["musica"].ListarPlaylists, requisicao)


class CrudGrpc(User):
    wait_time = constant(0.5)
    tasks = [CicloGrpc]