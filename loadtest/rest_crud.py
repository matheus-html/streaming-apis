from locust import HttpUser, constant

from comum import TIMEOUT
from crud_comum import CicloBase

CAMINHOS = {"usuario": "/usuarios", "musica": "/musicas", "playlist": "/playlists"}
RELACIONADOS = {
    "playlists_do_usuario": "/usuarios/{}/playlists",
    "musicas_da_playlist": "/playlists/{}/musicas",
    "playlists_da_musica": "/musicas/{}/playlists",
}


class CicloRest(CicloBase):
    def requisitar(self, metodo, caminho, nome, esperado, **opcoes):
        with self.client.request(
            metodo, caminho, name=nome, timeout=TIMEOUT, catch_response=True, **opcoes
        ) as resposta:
            if resposta.status_code != esperado:
                resposta.failure(f"http {resposta.status_code}")
                return None
            resposta.success()
            return resposta

    def criar(self, tipo, dados):
        resposta = self.requisitar("POST", CAMINHOS[tipo], f"criar {tipo}", 201, json=dados)
        return resposta.json()["id"] if resposta is not None else None

    def obter(self, tipo, identificador):
        self.requisitar("GET", f"{CAMINHOS[tipo]}/{identificador}", f"obter {tipo}", 200)

    def atualizar(self, tipo, identificador, dados):
        self.requisitar("PUT", f"{CAMINHOS[tipo]}/{identificador}", f"atualizar {tipo}", 200, json=dados)

    def remover(self, tipo, identificador):
        self.requisitar("DELETE", f"{CAMINHOS[tipo]}/{identificador}", f"remover {tipo}", 204)

    def relacionados(self, nome, identificador):
        self.requisitar("GET", RELACIONADOS[nome].format(identificador), nome, 200)


class CrudRest(HttpUser):
    wait_time = constant(0.5)
    tasks = [CicloRest]