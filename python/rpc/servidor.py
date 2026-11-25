import multiprocessing
import os
import signal
import sys
from concurrent import futures

import grpc
from grpc_reflection.v1alpha import reflection

from core import config

THREADS = int(os.environ.get("GRPC_THREADS", "40"))


def servir():
    from . import streaming_pb2 as pb
    from . import streaming_pb2_grpc as pb_grpc
    from .implementacao import MusicaServico, PlaylistServico, UsuarioServico

    servidor = grpc.server(
        futures.ThreadPoolExecutor(max_workers=THREADS), options=[("grpc.so_reuseport", 1)]
    )
    pb_grpc.add_UsuarioServiceServicer_to_server(UsuarioServico(), servidor)
    pb_grpc.add_MusicaServiceServicer_to_server(MusicaServico(), servidor)
    pb_grpc.add_PlaylistServiceServicer_to_server(PlaylistServico(), servidor)
    nomes = [servico.full_name for servico in pb.DESCRIPTOR.services_by_name.values()]
    reflection.enable_server_reflection(nomes + [reflection.SERVICE_NAME], servidor)
    servidor.add_insecure_port(f"0.0.0.0:{config.PORT}")
    servidor.start()
    servidor.wait_for_termination()


def principal():
    contexto = multiprocessing.get_context("spawn")
    processos = [contexto.Process(target=servir) for _ in range(config.WORKERS)]
    for processo in processos:
        processo.start()

    def encerrar(*_):
        for processo in processos:
            processo.terminate()
        sys.exit(0)

    signal.signal(signal.SIGTERM, encerrar)
    signal.signal(signal.SIGINT, encerrar)
    for processo in processos:
        processo.join()


if __name__ == "__main__":
    principal()