import os
import random
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import psycopg
from psycopg.types.json import Jsonb

HOST = os.environ.get("DB_HOST", "localhost")
PORTA = int(os.environ.get("DB_PORT", "5432"))
USUARIO = os.environ.get("DB_USER", "streaming")
SENHA = os.environ.get("DB_PASSWORD", "streaming")

BANCO_BASE = "streaming_base"
BANCO_FINAL = "streaming"

TOTAL_USUARIOS = int(os.environ.get("SEED_USUARIOS", "5000"))
TOTAL_MUSICAS = int(os.environ.get("SEED_MUSICAS", "20000"))
TOTAL_PLAYLISTS = int(os.environ.get("SEED_PLAYLISTS", "15000"))
MUSICAS_POR_PLAYLIST = (20, 60)
SEMENTE = 42

INICIO = datetime(2020, 1, 1, tzinfo=timezone.utc)
FIM = datetime(2026, 11, 1, tzinfo=timezone.utc)

PALAVRAS = [
    "amor", "noite", "luz", "mar", "vento", "estrada", "sonho", "fogo", "cidade", "chuva",
    "silêncio", "coração", "tempo", "caminho", "saudade", "verão", "estrela", "rua", "festa",
    "segredo", "distância", "memória", "ritmo", "céu", "terra", "sol", "lua", "janela",
    "história", "batida", "liberdade", "encontro", "horizonte", "aurora", "sombra", "viagem",
    "melodia", "fronteira", "pedra", "rio", "folha", "cor", "abraço", "jardim", "trem",
    "paixão", "lembrança", "dança", "coragem", "manhã", "tarde", "porto", "nuvem", "areia",
]
NOMES = [
    "Ana", "Bruno", "Carla", "Daniel", "Eduarda", "Felipe", "Gabriela", "Henrique", "Isabela",
    "João", "Karina", "Lucas", "Mariana", "Nicolas", "Olívia", "Pedro", "Rafaela", "Samuel",
    "Tatiana", "Vinícius", "Beatriz", "Caio", "Débora", "Eduardo", "Fernanda", "Gustavo",
    "Helena", "Igor", "Juliana", "Leonardo",
]
SOBRENOMES = [
    "Silva", "Souza", "Oliveira", "Santos", "Lima", "Pereira", "Costa", "Ribeiro", "Almeida",
    "Carvalho", "Gomes", "Martins", "Rocha", "Araújo", "Barbosa", "Cardoso", "Teixeira",
    "Moreira", "Nunes", "Vieira",
]
LOCAIS = [
    ("Brasil", ["Fortaleza", "São Paulo", "Recife", "Salvador", "Curitiba", "Belo Horizonte"]),
    ("Portugal", ["Lisboa", "Porto", "Coimbra"]),
    ("Argentina", ["Buenos Aires", "Córdoba"]),
    ("México", ["Cidade do México", "Guadalajara"]),
    ("Estados Unidos", ["Nova York", "Los Angeles", "Chicago"]),
    ("Japão", ["Tóquio", "Osaka"]),
]
PLANOS = ["gratuito", "premium", "familia", "estudante"]
IDIOMAS = ["pt", "en", "es", "fr", "ja", "ko"]
TEMAS = ["claro", "escuro", "sistema"]
GENEROS = [
    "rock", "pop", "mpb", "sertanejo", "funk", "forró", "samba", "jazz", "blues", "eletrônica",
    "hip hop", "reggae", "clássica", "metal", "indie", "folk", "soul", "country", "k-pop", "lo-fi",
]
TAGS = [
    "relaxar", "treino", "foco", "festa", "viagem", "romântica", "nostalgia", "acústico",
    "ao vivo", "remix", "instrumental", "clássicos", "novidades", "madrugada", "verão",
]
GRAVADORAS = ["Aurora Records", "Maré Música", "Horizonte Sound", "Nuvem Discos", "Estrela Label"]
DISPOSITIVOS = ["celular", "desktop", "tv", "caixa-de-som", "carro", "tablet"]
QUALIDADES = ["baixa", "normal", "alta", "lossless"]
TONALIDADES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
MODOS = ["maior", "menor"]


def frase(rng, minimo, maximo):
    return " ".join(rng.choice(PALAVRAS) for _ in range(rng.randint(minimo, maximo)))


def titulo(rng, minimo, maximo):
    return frase(rng, minimo, maximo).capitalize()


def pessoa(rng):
    return f"{rng.choice(NOMES)} {rng.choice(SOBRENOMES)}"


def instante(rng, inicio=INICIO, fim=FIM):
    segundos = int((fim - inicio).total_seconds())
    return inicio + timedelta(seconds=rng.randint(0, segundos))


def iso(momento):
    return momento.strftime("%Y-%m-%dT%H:%M:%SZ")


def gerar_artistas(rng):
    artistas = set()
    while len(artistas) < 600:
        if rng.random() < 0.5:
            artistas.add(pessoa(rng))
        else:
            artistas.add(f"{rng.choice(['Os', 'As', 'Banda', 'Trio', 'Grupo'])} {rng.choice(PALAVRAS).capitalize()} {rng.choice(PALAVRAS).capitalize()}")
    return sorted(artistas)


def gerar_usuario(rng, identificador):
    nome = rng.choice(NOMES)
    sobrenome = rng.choice(SOBRENOMES)
    pais, cidades = rng.choice(LOCAIS)
    cadastro = instante(rng)
    username = f"{nome.lower()}.{sobrenome.lower()}{identificador}"
    historico = [
        {
            "musicaId": rng.randint(1, TOTAL_MUSICAS),
            "iniciadaEm": iso(instante(rng, cadastro, FIM)),
            "duracaoOuvidaMs": rng.randint(15000, 420000),
            "dispositivo": rng.choice(DISPOSITIVOS),
        }
        for _ in range(20)
    ]
    preferencias = {
        "notificacoes": rng.random() < 0.6,
        "qualidadeAudio": rng.choice(QUALIDADES),
        "conteudoExplicito": rng.random() < 0.7,
        "crossfadeSegundos": rng.randint(0, 12),
        "modoOffline": rng.random() < 0.2,
    }
    return (
        identificador,
        f"{nome} {sobrenome}",
        rng.randint(13, 80),
        f"{username}@exemplo.com",
        username,
        pais,
        rng.choice(cidades),
        rng.choice(PLANOS),
        cadastro,
        instante(rng, cadastro, FIM),
        frase(rng, 25, 45).capitalize() + ".",
        rng.choice(IDIOMAS),
        rng.choice(TEMAS),
        rng.sample(GENEROS, rng.randint(2, 5)),
        f"https://cdn.exemplo.com/avatares/{identificador}.jpg",
        Jsonb(preferencias),
        Jsonb(historico),
    )


def gerar_musica(rng, identificador, artistas):
    ano = rng.randint(1970, 2026)
    letra = "\n".join(frase(rng, 7, 11).capitalize() for _ in range(30))
    audio = {
        "bpm": rng.randint(60, 190),
        "tonalidade": f"{rng.choice(TONALIDADES)} {rng.choice(MODOS)}",
        "energia": round(rng.random(), 3),
        "dancabilidade": round(rng.random(), 3),
        "valencia": round(rng.random(), 3),
        "acustica": round(rng.random(), 3),
    }
    isrc = "BR" + "".join(rng.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(3)) + f"{ano % 100:02d}{rng.randint(0, 99999):05d}"
    return (
        identificador,
        titulo(rng, 2, 4),
        rng.choice(artistas),
        titulo(rng, 1, 3),
        ano,
        rng.randint(1, 18),
        rng.randint(120000, 420000),
        rng.choice(GENEROS),
        rng.choice(IDIOMAS),
        rng.random() < 0.15,
        isrc,
        rng.choice(GRAVADORAS),
        rng.randint(0, 100),
        letra,
        [pessoa(rng) for _ in range(rng.randint(2, 4))],
        [pessoa(rng) for _ in range(rng.randint(1, 3))],
        rng.sample(TAGS, rng.randint(3, 6)),
        Jsonb(audio),
    )


def gerar_playlist(rng, identificador):
    criada = instante(rng)
    return (
        identificador,
        titulo(rng, 2, 4),
        rng.randint(1, TOTAL_USUARIOS),
        frase(rng, 15, 30).capitalize() + ".",
        rng.random() < 0.7,
        rng.random() < 0.2,
        criada,
        instante(rng, criada, FIM),
        f"https://cdn.exemplo.com/capas/{identificador}.jpg",
        rng.sample(TAGS, rng.randint(2, 5)),
    )


def conectar(banco, autocommit=False):
    return psycopg.connect(
        host=HOST, port=PORTA, user=USUARIO, password=SENHA, dbname=banco, autocommit=autocommit
    )


def recriar_bancos():
    with conectar("postgres", autocommit=True) as conexao:
        conexao.execute(f"DROP DATABASE IF EXISTS {BANCO_FINAL} WITH (FORCE)")
        conexao.execute(f"DROP DATABASE IF EXISTS {BANCO_BASE} WITH (FORCE)")
        conexao.execute(f"CREATE DATABASE {BANCO_BASE}")


def popular():
    rng = random.Random(SEMENTE)
    artistas = gerar_artistas(rng)
    esquema = (Path(__file__).parent / "schema.sql").read_text(encoding="utf-8")

    with conectar(BANCO_BASE) as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(esquema)

            cursor.executemany(
                "INSERT INTO usuario (id, nome, idade, email, username, pais, cidade, plano, "
                "data_cadastro, ultimo_acesso, bio, idioma, tema, generos_favoritos, avatar_url, "
                "preferencias, historico_recente) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (gerar_usuario(rng, i) for i in range(1, TOTAL_USUARIOS + 1)),
            )

            cursor.executemany(
                "INSERT INTO musica (id, nome, artista, album, ano_lancamento, numero_faixa, "
                "duracao_ms, genero, idioma, explicita, isrc, gravadora, popularidade, letra, "
                "compositores, produtores, tags, audio) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (gerar_musica(rng, i, artistas) for i in range(1, TOTAL_MUSICAS + 1)),
            )

            cursor.executemany(
                "INSERT INTO playlist (id, nome, usuario_id, descricao, publica, colaborativa, "
                "criada_em, atualizada_em, capa_url, tags) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (gerar_playlist(rng, i) for i in range(1, TOTAL_PLAYLISTS + 1)),
            )

            with cursor.copy(
                "COPY playlist_musica (playlist_id, musica_id, posicao) FROM STDIN"
            ) as copia:
                for playlist_id in range(1, TOTAL_PLAYLISTS + 1):
                    quantidade = rng.randint(*MUSICAS_POR_PLAYLIST)
                    escolhidas = rng.sample(range(1, TOTAL_MUSICAS + 1), quantidade)
                    for posicao, musica_id in enumerate(escolhidas, start=1):
                        copia.write_row((playlist_id, musica_id, posicao))

            for tabela in ("usuario", "musica", "playlist"):
                cursor.execute(
                    f"SELECT setval(pg_get_serial_sequence('{tabela}', 'id'), "
                    f"(SELECT max(id) FROM {tabela}))"
                )

    with conectar(BANCO_BASE, autocommit=True) as conexao:
        conexao.execute("ANALYZE")


def clonar_banco_final():
    with conectar("postgres", autocommit=True) as conexao:
        conexao.execute(f"CREATE DATABASE {BANCO_FINAL} TEMPLATE {BANCO_BASE}")


def resumir():
    with conectar(BANCO_FINAL) as conexao:
        for tabela in ("usuario", "musica", "playlist", "playlist_musica"):
            total = conexao.execute(f"SELECT count(*) FROM {tabela}").fetchone()[0]
            print(f"{tabela}: {total}")
        tamanho = conexao.execute(
            "SELECT pg_size_pretty(pg_database_size(current_database()))"
        ).fetchone()[0]
        print(f"tamanho do banco: {tamanho}")


def main():
    inicio = time.time()
    recriar_bancos()
    popular()
    clonar_banco_final()
    resumir()
    print(f"concluido em {time.time() - inicio:.1f}s")


if __name__ == "__main__":
    main()