import itertools
import os
import random
import sys
import time

import grpc
import grpc.experimental.gevent as grpc_gevent
import grpc_tools
from grpc_tools import protoc
from locust import User, constant, task

from comum import TIMEOUT, TOTAL_MUSICAS, TOTAL_PLAYLISTS, TOTAL_USUARIOS

grpc_gevent.init_gevent()

PASTA_PROTO = os.environ.get("PROTO_DIR", "/proto")
PASTA_STUBS = os.environ.get("STUBS_DIR", "/tmp/stubs")
CANAIS = int(os.environ.get("CANAIS", "32"))

os.makedirs(PASTA_STUBS, exist_ok=True)
PASTA_PADRAO = os.path.join(os.path.dirname(grpc_tools.__file__), "_proto")
protoc.main([
    "protoc", f"-I{PASTA_PROTO}", f"-I{PASTA_PADRAO}",
    f"--python_out={PASTA_STUBS}", f"--grpc_python_out={PASTA_STUBS}",
    f"{PASTA_PROTO}/streaming.proto",
])
sys.path.insert(0, PASTA_STUBS)

import streaming_pb2 as pb
import streaming_pb2_grpc as pb_grpc

canais = []
sorteio = itertools.count()


def obter_canal(alvo):
    if not canais:
        for _ in range(CANAIS):
            canais.append(grpc.insecure_channel(alvo))
    return canais[next(sorteio) % len(canais)]


class ConsultasGrpc(User):
    wait_time = constant(0.5)

    def on_start(self):
        alvo = self.host.split("://")[-1]
        canal = obter_canal(alvo)
        self.usuarios = pb_grpc.UsuarioServiceStub(canal)
        self.musicas = pb_grpc.MusicaServiceStub(canal)
        self.playlists = pb_grpc.PlaylistServiceStub(canal)

    def chamar(self, nome, metodo, requisicao):
        inicio = time.perf_counter()
        erro = None
        try:
            metodo(requisicao, timeout=TIMEOUT)
        except grpc.RpcError as excecao:
            erro = excecao
        self.environment.events.request.fire(
            request_type="gRPC",
            name=nome,
            response_time=(time.perf_counter() - inicio) * 1000,
            response_length=0,
            exception=erro,
            context={},
        )

    @task
    def usuario(self):
        self.chamar(
            "UsuarioService/Obter", self.usuarios.Obter,
            pb.IdRequisicao(id=random.randint(1, TOTAL_USUARIOS)),
        )

    @task
    def playlists_do_usuario(self):
        self.chamar(
            "UsuarioService/ListarPlaylists", self.usuarios.ListarPlaylists,
            pb.ListarRelacionadosRequisicao(id=random.randint(1, TOTAL_USUARIOS)),
        )

    @task
    def playlist(self):
        self.chamar(
            "PlaylistService/Obter", self.playlists.Obter,
            pb.IdRequisicao(id=random.randint(1, TOTAL_PLAYLISTS)),
        )

    @task
    def musicas_da_playlist(self):
        self.chamar(
            "PlaylistService/ListarMusicas", self.playlists.ListarMusicas,
            pb.ListarRelacionadosRequisicao(id=random.randint(1, TOTAL_PLAYLISTS)),
        )

    @task
    def playlists_da_musica(self):
        self.chamar(
            "MusicaService/ListarPlaylists", self.musicas.ListarPlaylists,
            pb.ListarRelacionadosRequisicao(id=random.randint(1, TOTAL_MUSICAS)),
        )