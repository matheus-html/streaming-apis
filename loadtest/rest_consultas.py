import random

from locust import HttpUser, constant, task

from comum import TIMEOUT, TOTAL_MUSICAS, TOTAL_PLAYLISTS, TOTAL_USUARIOS


class ConsultasRest(HttpUser):
    wait_time = constant(0.5)

    def consultar(self, caminho, nome):
        self.client.get(caminho, name=nome, timeout=TIMEOUT)

    @task
    def usuario_por_id(self):
        self.consultar(f"/usuarios/{random.randint(1, TOTAL_USUARIOS)}", "/usuarios/{id}")

    @task
    def playlists_do_usuario(self):
        self.consultar(
            f"/usuarios/{random.randint(1, TOTAL_USUARIOS)}/playlists", "/usuarios/{id}/playlists"
        )

    @task
    def playlist_por_id(self):
        self.consultar(f"/playlists/{random.randint(1, TOTAL_PLAYLISTS)}", "/playlists/{id}")

    @task
    def musicas_da_playlist(self):
        self.consultar(
            f"/playlists/{random.randint(1, TOTAL_PLAYLISTS)}/musicas", "/playlists/{id}/musicas"
        )

    @task
    def playlists_da_musica(self):
        self.consultar(
            f"/musicas/{random.randint(1, TOTAL_MUSICAS)}/playlists", "/musicas/{id}/playlists"
        )