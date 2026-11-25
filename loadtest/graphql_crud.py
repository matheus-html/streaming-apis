from locust import HttpUser, constant

from comum import TIMEOUT
from crud_comum import CicloBase
from graphql_consultas import MUSICA, PLAYLIST, USUARIO

CAMPOS = {"usuario": USUARIO, "musica": MUSICA, "playlist": PLAYLIST}
NOMES = {"usuario": "Usuario", "musica": "Musica", "playlist": "Playlist"}
RELACIONADOS = {
    "playlists_do_usuario": (
        "query($id: Int!) { playlistsDoUsuario(usuarioId: $id) { itens { %s } pagina tamanho total } }" % PLAYLIST
    ),
    "musicas_da_playlist": (
        "query($id: Int!) { musicasDaPlaylist(playlistId: $id) { itens { %s } pagina tamanho total } }" % MUSICA
    ),
    "playlists_da_musica": (
        "query($id: Int!) { playlistsDaMusica(musicaId: $id) { itens { %s } pagina tamanho total } }" % PLAYLIST
    ),
}


def criacao(tipo):
    n = NOMES[tipo]
    return "mutation($e: %sEntrada!) { criar%s(entrada: $e) { %s } }" % (n, n, CAMPOS[tipo])


def atualizacao(tipo):
    n = NOMES[tipo]
    return "mutation($id: Int!, $e: %sEntrada!) { atualizar%s(id: $id, entrada: $e) { %s } }" % (n, n, CAMPOS[tipo])


def remocao(tipo):
    n = NOMES[tipo]
    return "mutation($id: Int!) { remover%s(id: $id) }" % n


def obtencao(tipo):
    return "query($id: Int!) { %s(id: $id) { %s } }" % (tipo, CAMPOS[tipo])


class CicloGraphql(CicloBase):
    def executar(self, nome, consulta, variaveis):
        with self.client.post(
            "/graphql",
            json={"query": consulta, "variables": variaveis},
            name=nome,
            timeout=TIMEOUT,
            catch_response=True,
        ) as resposta:
            if resposta.status_code != 200:
                resposta.failure(f"http {resposta.status_code}")
                return None
            corpo = resposta.json()
            if corpo.get("errors"):
                resposta.failure("erro graphql")
                return None
            resposta.success()
            return corpo["data"]

    def criar(self, tipo, dados):
        dados_resposta = self.executar(f"criar {tipo}", criacao(tipo), {"e": dados})
        return dados_resposta[f"criar{NOMES[tipo]}"]["id"] if dados_resposta else None

    def obter(self, tipo, identificador):
        self.executar(f"obter {tipo}", obtencao(tipo), {"id": identificador})

    def atualizar(self, tipo, identificador, dados):
        self.executar(f"atualizar {tipo}", atualizacao(tipo), {"id": identificador, "e": dados})

    def remover(self, tipo, identificador):
        self.executar(f"remover {tipo}", remocao(tipo), {"id": identificador})

    def relacionados(self, nome, identificador):
        self.executar(nome, RELACIONADOS[nome], {"id": identificador})


class CrudGraphql(HttpUser):
    wait_time = constant(0.5)
    tasks = [CicloGraphql]