import random
import uuid

from locust import SequentialTaskSet, task

from comum import TOTAL_MUSICAS, TOTAL_PLAYLISTS, TOTAL_USUARIOS

GENEROS = ["rock", "pop", "jazz", "samba", "eletronica", "mpb", "forro", "classica"]


def sufixo():
    return uuid.uuid4().hex[:12]


def dados_usuario():
    s = sufixo()
    return {
        "nome": f"Carga {s}",
        "idade": random.randint(14, 80),
        "email": f"{s}@carga.teste",
        "username": f"carga_{s}",
        "pais": "BR",
        "cidade": "Fortaleza",
        "plano": "gratuito",
        "bio": "usuario criado pelo teste de carga",
        "idioma": "pt",
        "tema": "escuro",
        "generosFavoritos": random.sample(GENEROS, 3),
        "avatarUrl": f"https://exemplo.test/{s}.png",
        "preferencias": {
            "notificacoes": True,
            "qualidadeAudio": "alta",
            "conteudoExplicito": False,
            "crossfadeSegundos": random.randint(0, 12),
            "modoOffline": False,
        },
        "historicoRecente": [
            {
                "musicaId": random.randint(1, TOTAL_MUSICAS),
                "iniciadaEm": "2026-01-01T12:00:00Z",
                "duracaoOuvidaMs": random.randint(30000, 240000),
                "dispositivo": "celular",
            }
        ],
    }


def dados_musica():
    s = sufixo()
    return {
        "nome": f"Faixa {s}",
        "artista": f"Artista {s[:6]}",
        "album": f"Album {s[:6]}",
        "anoLancamento": random.randint(1970, 2026),
        "numeroFaixa": random.randint(1, 20),
        "duracaoMs": random.randint(90000, 360000),
        "genero": random.choice(GENEROS),
        "idioma": "pt",
        "explicita": False,
        "isrc": f"BR{s[:10].upper()}",
        "gravadora": "Gravadora de Carga",
        "popularidade": random.randint(0, 100),
        "letra": "letra de teste para o teste de carga",
        "compositores": [f"Compositor {s[:4]}"],
        "produtores": [f"Produtor {s[:4]}"],
        "tags": ["carga", random.choice(GENEROS)],
        "audio": {
            "bpm": random.randint(60, 180),
            "tonalidade": "C",
            "energia": 0.5,
            "dancabilidade": 0.5,
            "valencia": 0.5,
            "acustica": 0.25,
        },
    }


def dados_playlist(usuario_id, musica_ids):
    s = sufixo()
    return {
        "nome": f"Playlist {s}",
        "usuarioId": usuario_id,
        "descricao": "playlist criada pelo teste de carga",
        "publica": True,
        "colaborativa": False,
        "capaUrl": f"https://exemplo.test/{s}.jpg",
        "tags": ["carga"],
        "musicaIds": musica_ids,
    }


def musicas_sorteadas(quantidade):
    return random.sample(range(1, TOTAL_MUSICAS + 1), quantidade)


class CicloBase(SequentialTaskSet):
    def on_start(self):
        self.reiniciar()

    def reiniciar(self):
        self.usuario = None
        self.musica = None
        self.playlist = None

    @task
    def criar_usuario(self):
        self.usuario = self.criar("usuario", dados_usuario())

    @task
    def criar_musica(self):
        self.musica = self.criar("musica", dados_musica())

    @task
    def criar_playlist(self):
        if self.usuario and self.musica:
            self.playlist = self.criar(
                "playlist", dados_playlist(self.usuario, [self.musica, *musicas_sorteadas(2)])
            )

    @task
    def obter_usuario(self):
        if self.usuario:
            self.obter("usuario", self.usuario)

    @task
    def obter_playlist(self):
        if self.playlist:
            self.obter("playlist", self.playlist)

    @task
    def atualizar_usuario(self):
        if self.usuario:
            self.atualizar(
                "usuario", self.usuario,
                {"bio": f"bio atualizada {sufixo()}", "idade": random.randint(14, 80), "plano": "premium"},
            )

    @task
    def atualizar_playlist(self):
        if self.playlist:
            self.atualizar(
                "playlist", self.playlist,
                {"descricao": f"descricao atualizada {sufixo()}", "musicaIds": [self.musica, *musicas_sorteadas(1)]},
            )

    @task
    def playlists_do_usuario(self):
        self.relacionados("playlists_do_usuario", random.randint(1, TOTAL_USUARIOS))

    @task
    def musicas_da_playlist(self):
        self.relacionados("musicas_da_playlist", random.randint(1, TOTAL_PLAYLISTS))

    @task
    def playlists_da_musica(self):
        self.relacionados("playlists_da_musica", random.randint(1, TOTAL_MUSICAS))

    @task
    def remover_playlist(self):
        if self.playlist:
            self.remover("playlist", self.playlist)

    @task
    def remover_musica(self):
        if self.musica:
            self.remover("musica", self.musica)

    @task
    def remover_usuario(self):
        if self.usuario:
            self.remover("usuario", self.usuario)
        self.reiniciar()