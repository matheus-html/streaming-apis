import grpc
from google.protobuf import json_format

from core import servicos
from core.erros import Conflito, Invalido, NaoEncontrado

from . import streaming_pb2 as pb
from . import streaming_pb2_grpc as pb_grpc

TIPOS_LISTA = {"ListaTexto", "ListaInteiros"}


def _camel(nome):
    partes = nome.split("_")
    return partes[0] + "".join(p.capitalize() for p in partes[1:])


def como_dados(entrada):
    dados = {}
    for campo in entrada.DESCRIPTOR.fields:
        if not entrada.HasField(campo.name):
            continue
        valor = getattr(entrada, campo.name)
        if campo.message_type is not None:
            if campo.message_type.name in TIPOS_LISTA:
                valor = list(valor.valores)
            else:
                valor = json_format.MessageToDict(valor)
        dados[_camel(campo.name)] = valor
    return dados


def opcional(mensagem, nome):
    return getattr(mensagem, nome) if mensagem.HasField(nome) else None


def executar(contexto, funcao, *argumentos):
    try:
        return funcao(*argumentos)
    except NaoEncontrado as erro:
        contexto.abort(grpc.StatusCode.NOT_FOUND, str(erro))
    except Invalido as erro:
        contexto.abort(grpc.StatusCode.INVALID_ARGUMENT, str(erro))
    except Conflito as erro:
        contexto.abort(grpc.StatusCode.FAILED_PRECONDITION, str(erro))


def para_mensagem(dados, tipo):
    return json_format.ParseDict(dados, tipo())


def listar(contexto, recurso, requisicao, tipo):
    dados = executar(
        contexto, recurso.listar,
        opcional(requisicao, "pagina"), opcional(requisicao, "tamanho"), opcional(requisicao, "nome"),
    )
    return para_mensagem(dados, tipo)


def relacionados(contexto, funcao, requisicao, tipo):
    dados = executar(
        contexto, funcao, requisicao.id, opcional(requisicao, "pagina"), opcional(requisicao, "tamanho")
    )
    return para_mensagem(dados, tipo)


class UsuarioServico(pb_grpc.UsuarioServiceServicer):
    def Listar(self, requisicao, contexto):
        return listar(contexto, servicos.usuarios, requisicao, pb.PaginaUsuarios)

    def Obter(self, requisicao, contexto):
        return para_mensagem(executar(contexto, servicos.usuarios.obter, requisicao.id), pb.Usuario)

    def Criar(self, requisicao, contexto):
        return para_mensagem(executar(contexto, servicos.usuarios.criar, como_dados(requisicao)), pb.Usuario)

    def Atualizar(self, requisicao, contexto):
        dados = executar(
            contexto, servicos.usuarios.atualizar, requisicao.id, como_dados(requisicao.entrada)
        )
        return para_mensagem(dados, pb.Usuario)

    def Remover(self, requisicao, contexto):
        executar(contexto, servicos.usuarios.remover, requisicao.id)
        return pb.Vazio()

    def ListarPlaylists(self, requisicao, contexto):
        return relacionados(contexto, servicos.playlists_do_usuario, requisicao, pb.PaginaPlaylists)


class MusicaServico(pb_grpc.MusicaServiceServicer):
    def Listar(self, requisicao, contexto):
        return listar(contexto, servicos.musicas, requisicao, pb.PaginaMusicas)

    def Obter(self, requisicao, contexto):
        return para_mensagem(executar(contexto, servicos.musicas.obter, requisicao.id), pb.Musica)

    def Criar(self, requisicao, contexto):
        return para_mensagem(executar(contexto, servicos.musicas.criar, como_dados(requisicao)), pb.Musica)

    def Atualizar(self, requisicao, contexto):
        dados = executar(
            contexto, servicos.musicas.atualizar, requisicao.id, como_dados(requisicao.entrada)
        )
        return para_mensagem(dados, pb.Musica)

    def Remover(self, requisicao, contexto):
        executar(contexto, servicos.musicas.remover, requisicao.id)
        return pb.Vazio()

    def ListarPlaylists(self, requisicao, contexto):
        return relacionados(contexto, servicos.playlists_da_musica, requisicao, pb.PaginaPlaylists)


class PlaylistServico(pb_grpc.PlaylistServiceServicer):
    def Listar(self, requisicao, contexto):
        return listar(contexto, servicos.playlists, requisicao, pb.PaginaPlaylists)

    def Obter(self, requisicao, contexto):
        return para_mensagem(executar(contexto, servicos.playlists.obter, requisicao.id), pb.Playlist)

    def Criar(self, requisicao, contexto):
        return para_mensagem(
            executar(contexto, servicos.playlists.criar, como_dados(requisicao)), pb.Playlist
        )

    def Atualizar(self, requisicao, contexto):
        dados = executar(
            contexto, servicos.playlists.atualizar, requisicao.id, como_dados(requisicao.entrada)
        )
        return para_mensagem(dados, pb.Playlist)

    def Remover(self, requisicao, contexto):
        executar(contexto, servicos.playlists.remover, requisicao.id)
        return pb.Vazio()

    def ListarMusicas(self, requisicao, contexto):
        return relacionados(contexto, servicos.musicas_da_playlist, requisicao, pb.PaginaMusicas)