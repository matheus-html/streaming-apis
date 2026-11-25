from .recursos import Campo, Recurso, RecursoPlaylist

usuarios = Recurso(
    "usuário",
    "usuario",
    [
        Campo("id", "id", "id"),
        Campo("nome", "nome", "texto", obrigatorio=True),
        Campo("idade", "idade", "inteiro", obrigatorio=True),
        Campo("email", "email", "texto"),
        Campo("username", "username", "texto"),
        Campo("pais", "pais", "texto"),
        Campo("cidade", "cidade", "texto"),
        Campo("plano", "plano", "texto", padrao="gratuito"),
        Campo("dataCadastro", "data_cadastro", "instante", automatico="criacao"),
        Campo("ultimoAcesso", "ultimo_acesso", "instante", automatico="ambos"),
        Campo("bio", "bio", "texto"),
        Campo("idioma", "idioma", "texto", padrao="pt"),
        Campo("tema", "tema", "texto", padrao="sistema"),
        Campo("generosFavoritos", "generos_favoritos", "lista"),
        Campo("avatarUrl", "avatar_url", "texto"),
        Campo("preferencias", "preferencias", "json"),
        Campo("historicoRecente", "historico_recente", "json", padrao=[]),
    ],
)

musicas = Recurso(
    "música",
    "musica",
    [
        Campo("id", "id", "id"),
        Campo("nome", "nome", "texto", obrigatorio=True),
        Campo("artista", "artista", "texto", obrigatorio=True),
        Campo("album", "album", "texto"),
        Campo("anoLancamento", "ano_lancamento", "inteiro"),
        Campo("numeroFaixa", "numero_faixa", "inteiro"),
        Campo("duracaoMs", "duracao_ms", "inteiro"),
        Campo("genero", "genero", "texto"),
        Campo("idioma", "idioma", "texto", padrao="pt"),
        Campo("explicita", "explicita", "booleano"),
        Campo("isrc", "isrc", "texto"),
        Campo("gravadora", "gravadora", "texto"),
        Campo("popularidade", "popularidade", "inteiro"),
        Campo("letra", "letra", "texto"),
        Campo("compositores", "compositores", "lista"),
        Campo("produtores", "produtores", "lista"),
        Campo("tags", "tags", "lista"),
        Campo("audio", "audio", "json"),
    ],
    colunas_busca=("nome", "artista"),
)

playlists = RecursoPlaylist(
    "playlist",
    "playlist",
    [
        Campo("id", "id", "id"),
        Campo("nome", "nome", "texto", obrigatorio=True),
        Campo("usuarioId", "usuario_id", "inteiro", obrigatorio=True),
        Campo("descricao", "descricao", "texto"),
        Campo("publica", "publica", "booleano"),
        Campo("colaborativa", "colaborativa", "booleano"),
        Campo("criadaEm", "criada_em", "instante", automatico="criacao"),
        Campo("atualizadaEm", "atualizada_em", "instante", automatico="ambos"),
        Campo("capaUrl", "capa_url", "texto"),
        Campo("tags", "tags", "lista"),
    ],
    extras_select=[
        '(SELECT count(*) FROM playlist_musica pm WHERE pm.playlist_id = t.id) AS "totalMusicas"',
        'COALESCE((SELECT sum(m.duracao_ms) FROM playlist_musica pm '
        'JOIN musica m ON m.id = pm.musica_id WHERE pm.playlist_id = t.id), 0) AS "duracaoTotalMs"',
        'ARRAY(SELECT pm.musica_id FROM playlist_musica pm '
        'WHERE pm.playlist_id = t.id ORDER BY pm.posicao) AS "musicaIds"',
    ],
)


def playlists_do_usuario(usuario_id, pagina=None, tamanho=None):
    return playlists.consultar(
        "", "WHERE t.usuario_id = %s", [usuario_id], "t.id", pagina, tamanho,
        pai=("usuario", "usuário", usuario_id),
    )


def musicas_da_playlist(playlist_id, pagina=None, tamanho=None):
    return musicas.consultar(
        "JOIN playlist_musica vinc ON vinc.musica_id = t.id",
        "WHERE vinc.playlist_id = %s", [playlist_id], "vinc.posicao", pagina, tamanho,
        pai=("playlist", "playlist", playlist_id),
    )


def playlists_da_musica(musica_id, pagina=None, tamanho=None):
    return playlists.consultar(
        "JOIN playlist_musica vinc ON vinc.playlist_id = t.id",
        "WHERE vinc.musica_id = %s", [musica_id], "t.id", pagina, tamanho,
        pai=("musica", "música", musica_id),
    )