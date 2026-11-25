import re
from typing import Generic, Optional, TypeVar

import anyio.to_thread
import strawberry
from graphql import GraphQLError
from strawberry.scalars import JSON

from core import servicos
from core.erros import Conflito, Invalido, NaoEncontrado

T = TypeVar("T")


def _snake(nome):
    return re.sub(r"([A-Z])", lambda m: "_" + m.group(1).lower(), nome)


def _camel(nome):
    partes = nome.split("_")
    return partes[0] + "".join(p.capitalize() for p in partes[1:])


@strawberry.type
class Usuario:
    id: int
    nome: str
    idade: int
    email: str
    username: str
    pais: str
    cidade: str
    plano: str
    data_cadastro: str
    ultimo_acesso: str
    bio: str
    idioma: str
    tema: str
    generos_favoritos: list[str]
    avatar_url: str
    preferencias: JSON
    historico_recente: JSON


@strawberry.type
class Musica:
    id: int
    nome: str
    artista: str
    album: str
    ano_lancamento: int
    numero_faixa: int
    duracao_ms: int
    genero: str
    idioma: str
    explicita: bool
    isrc: str
    gravadora: str
    popularidade: int
    letra: str
    compositores: list[str]
    produtores: list[str]
    tags: list[str]
    audio: JSON


@strawberry.type
class Playlist:
    id: int
    nome: str
    usuario_id: int
    descricao: str
    publica: bool
    colaborativa: bool
    criada_em: str
    atualizada_em: str
    capa_url: str
    tags: list[str]
    total_musicas: int
    duracao_total_ms: int
    musica_ids: list[int]


@strawberry.type
class Pagina(Generic[T]):
    itens: list[T]
    pagina: int
    tamanho: int
    total: int


@strawberry.input
class UsuarioEntrada:
    nome: Optional[str] = strawberry.UNSET
    idade: Optional[int] = strawberry.UNSET
    email: Optional[str] = strawberry.UNSET
    username: Optional[str] = strawberry.UNSET
    pais: Optional[str] = strawberry.UNSET
    cidade: Optional[str] = strawberry.UNSET
    plano: Optional[str] = strawberry.UNSET
    bio: Optional[str] = strawberry.UNSET
    idioma: Optional[str] = strawberry.UNSET
    tema: Optional[str] = strawberry.UNSET
    generos_favoritos: Optional[list[str]] = strawberry.UNSET
    avatar_url: Optional[str] = strawberry.UNSET
    preferencias: Optional[JSON] = strawberry.UNSET
    historico_recente: Optional[JSON] = strawberry.UNSET


@strawberry.input
class MusicaEntrada:
    nome: Optional[str] = strawberry.UNSET
    artista: Optional[str] = strawberry.UNSET
    album: Optional[str] = strawberry.UNSET
    ano_lancamento: Optional[int] = strawberry.UNSET
    numero_faixa: Optional[int] = strawberry.UNSET
    duracao_ms: Optional[int] = strawberry.UNSET
    genero: Optional[str] = strawberry.UNSET
    idioma: Optional[str] = strawberry.UNSET
    explicita: Optional[bool] = strawberry.UNSET
    isrc: Optional[str] = strawberry.UNSET
    gravadora: Optional[str] = strawberry.UNSET
    popularidade: Optional[int] = strawberry.UNSET
    letra: Optional[str] = strawberry.UNSET
    compositores: Optional[list[str]] = strawberry.UNSET
    produtores: Optional[list[str]] = strawberry.UNSET
    tags: Optional[list[str]] = strawberry.UNSET
    audio: Optional[JSON] = strawberry.UNSET


@strawberry.input
class PlaylistEntrada:
    nome: Optional[str] = strawberry.UNSET
    usuario_id: Optional[int] = strawberry.UNSET
    descricao: Optional[str] = strawberry.UNSET
    publica: Optional[bool] = strawberry.UNSET
    colaborativa: Optional[bool] = strawberry.UNSET
    capa_url: Optional[str] = strawberry.UNSET
    tags: Optional[list[str]] = strawberry.UNSET
    musica_ids: Optional[list[int]] = strawberry.UNSET


def converter(tipo, linha):
    return tipo(**{_snake(chave): valor for chave, valor in linha.items()})


def como_pagina(tipo, dados):
    return Pagina(
        itens=[converter(tipo, item) for item in dados["itens"]],
        pagina=dados["pagina"],
        tamanho=dados["tamanho"],
        total=dados["total"],
    )


def como_dados(entrada):
    return {
        _camel(chave): valor
        for chave, valor in vars(entrada).items()
        if valor is not strawberry.UNSET
    }


async def executar(funcao, *argumentos):
    try:
        return await anyio.to_thread.run_sync(funcao, *argumentos)
    except NaoEncontrado as erro:
        raise GraphQLError(str(erro), extensions={"codigo": "NAO_ENCONTRADO"}) from None
    except Invalido as erro:
        raise GraphQLError(str(erro), extensions={"codigo": "ENTRADA_INVALIDA"}) from None
    except Conflito as erro:
        raise GraphQLError(str(erro), extensions={"codigo": "CONFLITO"}) from None


@strawberry.type
class Query:
    @strawberry.field
    async def usuarios(
        self, pagina: Optional[int] = None, tamanho: Optional[int] = None, nome: Optional[str] = None
    ) -> Pagina[Usuario]:
        return como_pagina(Usuario, await executar(servicos.usuarios.listar, pagina, tamanho, nome))

    @strawberry.field
    async def usuario(self, id: int) -> Usuario:
        return converter(Usuario, await executar(servicos.usuarios.obter, id))

    @strawberry.field
    async def musicas(
        self, pagina: Optional[int] = None, tamanho: Optional[int] = None, nome: Optional[str] = None
    ) -> Pagina[Musica]:
        return como_pagina(Musica, await executar(servicos.musicas.listar, pagina, tamanho, nome))

    @strawberry.field
    async def musica(self, id: int) -> Musica:
        return converter(Musica, await executar(servicos.musicas.obter, id))

    @strawberry.field
    async def playlists(
        self, pagina: Optional[int] = None, tamanho: Optional[int] = None, nome: Optional[str] = None
    ) -> Pagina[Playlist]:
        return como_pagina(Playlist, await executar(servicos.playlists.listar, pagina, tamanho, nome))

    @strawberry.field
    async def playlist(self, id: int) -> Playlist:
        return converter(Playlist, await executar(servicos.playlists.obter, id))

    @strawberry.field
    async def playlists_do_usuario(
        self, usuario_id: int, pagina: Optional[int] = None, tamanho: Optional[int] = None
    ) -> Pagina[Playlist]:
        dados = await executar(servicos.playlists_do_usuario, usuario_id, pagina, tamanho)
        return como_pagina(Playlist, dados)

    @strawberry.field
    async def musicas_da_playlist(
        self, playlist_id: int, pagina: Optional[int] = None, tamanho: Optional[int] = None
    ) -> Pagina[Musica]:
        dados = await executar(servicos.musicas_da_playlist, playlist_id, pagina, tamanho)
        return como_pagina(Musica, dados)

    @strawberry.field
    async def playlists_da_musica(
        self, musica_id: int, pagina: Optional[int] = None, tamanho: Optional[int] = None
    ) -> Pagina[Playlist]:
        dados = await executar(servicos.playlists_da_musica, musica_id, pagina, tamanho)
        return como_pagina(Playlist, dados)


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def criar_usuario(self, entrada: UsuarioEntrada) -> Usuario:
        return converter(Usuario, await executar(servicos.usuarios.criar, como_dados(entrada)))

    @strawberry.mutation
    async def atualizar_usuario(self, id: int, entrada: UsuarioEntrada) -> Usuario:
        return converter(Usuario, await executar(servicos.usuarios.atualizar, id, como_dados(entrada)))

    @strawberry.mutation
    async def remover_usuario(self, id: int) -> bool:
        await executar(servicos.usuarios.remover, id)
        return True

    @strawberry.mutation
    async def criar_musica(self, entrada: MusicaEntrada) -> Musica:
        return converter(Musica, await executar(servicos.musicas.criar, como_dados(entrada)))

    @strawberry.mutation
    async def atualizar_musica(self, id: int, entrada: MusicaEntrada) -> Musica:
        return converter(Musica, await executar(servicos.musicas.atualizar, id, como_dados(entrada)))

    @strawberry.mutation
    async def remover_musica(self, id: int) -> bool:
        await executar(servicos.musicas.remover, id)
        return True

    @strawberry.mutation
    async def criar_playlist(self, entrada: PlaylistEntrada) -> Playlist:
        return converter(Playlist, await executar(servicos.playlists.criar, como_dados(entrada)))

    @strawberry.mutation
    async def atualizar_playlist(self, id: int, entrada: PlaylistEntrada) -> Playlist:
        return converter(Playlist, await executar(servicos.playlists.atualizar, id, como_dados(entrada)))

    @strawberry.mutation
    async def remover_playlist(self, id: int) -> bool:
        await executar(servicos.playlists.remover, id)
        return True


esquema = strawberry.Schema(query=Query, mutation=Mutation)