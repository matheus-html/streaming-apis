import random

from locust import HttpUser, constant, task

from comum import TIMEOUT, TOTAL_MUSICAS, TOTAL_PLAYLISTS, TOTAL_USUARIOS

USUARIO = (
    "id nome idade email username pais cidade plano dataCadastro ultimoAcesso bio idioma tema "
    "generosFavoritos avatarUrl preferencias historicoRecente"
)
MUSICA = (
    "id nome artista album anoLancamento numeroFaixa duracaoMs genero idioma explicita isrc gravadora "
    "popularidade letra compositores produtores tags audio"
)
PLAYLIST = (
    "id nome usuarioId descricao publica colaborativa criadaEm atualizadaEm capaUrl tags "
    "totalMusicas duracaoTotalMs musicaIds"
)

CONSULTAS = {
    "usuario": "query($id: Int!) { usuario(id: $id) { %s } }" % USUARIO,
    "playlistsDoUsuario": "query($id: Int!) { playlistsDoUsuario(usuarioId: $id) { itens { %s } pagina tamanho total } }" % PLAYLIST,
    "playlist": "query($id: Int!) { playlist(id: $id) { %s } }" % PLAYLIST,
    "musicasDaPlaylist": "query($id: Int!) { musicasDaPlaylist(playlistId: $id) { itens { %s } pagina tamanho total } }" % MUSICA,
    "playlistsDaMusica": "query($id: Int!) { playlistsDaMusica(musicaId: $id) { itens { %s } pagina tamanho total } }" % PLAYLIST,
}


class ConsultasGraphql(HttpUser):
    wait_time = constant(0.5)

    def consultar(self, nome, identificador):
        with self.client.post(
            "/graphql",
            json={"query": CONSULTAS[nome], "variables": {"id": identificador}},
            name=nome,
            timeout=TIMEOUT,
            catch_response=True,
        ) as resposta:
            if resposta.status_code != 200:
                resposta.failure(f"http {resposta.status_code}")
            elif b'"errors"' in resposta.content:
                resposta.failure("erro graphql")
            else:
                resposta.success()

    @task
    def usuario(self):
        self.consultar("usuario", random.randint(1, TOTAL_USUARIOS))

    @task
    def playlists_do_usuario(self):
        self.consultar("playlistsDoUsuario", random.randint(1, TOTAL_USUARIOS))

    @task
    def playlist(self):
        self.consultar("playlist", random.randint(1, TOTAL_PLAYLISTS))

    @task
    def musicas_da_playlist(self):
        self.consultar("musicasDaPlaylist", random.randint(1, TOTAL_PLAYLISTS))

    @task
    def playlists_da_musica(self):
        self.consultar("playlistsDaMusica", random.randint(1, TOTAL_MUSICAS))