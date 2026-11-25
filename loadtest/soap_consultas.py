import random

from locust import HttpUser, constant, task

from comum import TIMEOUT, TOTAL_MUSICAS, TOTAL_PLAYLISTS, TOTAL_USUARIOS

NS = "urn:streaming"
CABECALHO = {"Content-Type": "text/xml; charset=utf-8"}
MODELO = (
    '<?xml version="1.0" encoding="utf-8"?>'
    '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tns="urn:streaming">'
    "<soapenv:Body><tns:{operacao}><tns:id>{id}</tns:id></tns:{operacao}></soapenv:Body></soapenv:Envelope>"
)


class ConsultasSoap(HttpUser):
    wait_time = constant(0.5)

    def chamar(self, operacao, identificador):
        with self.client.post(
            "/soap",
            data=MODELO.format(operacao=operacao, id=identificador).encode("utf-8"),
            headers={**CABECALHO, "SOAPAction": f'"{NS}/{operacao}"'},
            name=operacao,
            timeout=TIMEOUT,
            catch_response=True,
        ) as resposta:
            if resposta.status_code != 200:
                resposta.failure(f"http {resposta.status_code}")
            elif b"Fault" in resposta.content[:400]:
                resposta.failure("soap fault")
            else:
                resposta.success()

    @task
    def usuario(self):
        self.chamar("ObterUsuario", random.randint(1, TOTAL_USUARIOS))

    @task
    def playlists_do_usuario(self):
        self.chamar("ListarPlaylistsDoUsuario", random.randint(1, TOTAL_USUARIOS))

    @task
    def playlist(self):
        self.chamar("ObterPlaylist", random.randint(1, TOTAL_PLAYLISTS))

    @task
    def musicas_da_playlist(self):
        self.chamar("ListarMusicasDaPlaylist", random.randint(1, TOTAL_PLAYLISTS))

    @task
    def playlists_da_musica(self):
        self.chamar("ListarPlaylistsDaMusica", random.randint(1, TOTAL_MUSICAS))