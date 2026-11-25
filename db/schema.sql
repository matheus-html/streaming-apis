CREATE TABLE usuario (
    id                SERIAL PRIMARY KEY,
    nome              TEXT        NOT NULL,
    idade             INTEGER     NOT NULL CHECK (idade BETWEEN 0 AND 130),
    email             TEXT        NOT NULL,
    username          TEXT        NOT NULL,
    pais              TEXT        NOT NULL,
    cidade            TEXT        NOT NULL,
    plano             TEXT        NOT NULL,
    data_cadastro     TIMESTAMPTZ NOT NULL,
    ultimo_acesso     TIMESTAMPTZ NOT NULL,
    bio               TEXT        NOT NULL,
    idioma            TEXT        NOT NULL,
    tema              TEXT        NOT NULL,
    generos_favoritos TEXT[]      NOT NULL,
    avatar_url        TEXT        NOT NULL,
    preferencias      JSONB       NOT NULL,
    historico_recente JSONB       NOT NULL
);

CREATE TABLE musica (
    id              SERIAL PRIMARY KEY,
    nome            TEXT     NOT NULL,
    artista         TEXT     NOT NULL,
    album           TEXT     NOT NULL,
    ano_lancamento  INTEGER  NOT NULL,
    numero_faixa    INTEGER  NOT NULL,
    duracao_ms      INTEGER  NOT NULL,
    genero          TEXT     NOT NULL,
    idioma          TEXT     NOT NULL,
    explicita       BOOLEAN  NOT NULL,
    isrc            TEXT     NOT NULL,
    gravadora       TEXT     NOT NULL,
    popularidade    INTEGER  NOT NULL CHECK (popularidade BETWEEN 0 AND 100),
    letra           TEXT     NOT NULL,
    compositores    TEXT[]   NOT NULL,
    produtores      TEXT[]   NOT NULL,
    tags            TEXT[]   NOT NULL,
    audio           JSONB    NOT NULL
);

CREATE TABLE playlist (
    id            SERIAL PRIMARY KEY,
    nome          TEXT        NOT NULL,
    usuario_id    INTEGER     NOT NULL REFERENCES usuario (id) ON DELETE CASCADE,
    descricao     TEXT        NOT NULL,
    publica       BOOLEAN     NOT NULL,
    colaborativa  BOOLEAN     NOT NULL,
    criada_em     TIMESTAMPTZ NOT NULL,
    atualizada_em TIMESTAMPTZ NOT NULL,
    capa_url      TEXT        NOT NULL,
    tags          TEXT[]      NOT NULL
);

CREATE TABLE playlist_musica (
    playlist_id INTEGER NOT NULL REFERENCES playlist (id) ON DELETE CASCADE,
    musica_id   INTEGER NOT NULL REFERENCES musica (id) ON DELETE RESTRICT,
    posicao     INTEGER NOT NULL,
    PRIMARY KEY (playlist_id, musica_id)
);

CREATE INDEX idx_playlist_usuario ON playlist (usuario_id);
CREATE INDEX idx_playlist_musica_musica ON playlist_musica (musica_id);
CREATE INDEX idx_playlist_musica_posicao ON playlist_musica (playlist_id, posicao);