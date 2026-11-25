package streaming.core;

import java.util.List;

public final class Servicos {

    public static final Recurso USUARIOS = new Recurso(
            "usuário",
            "usuario",
            List.of(
                    Campo.de("id", "id", "id"),
                    Campo.de("nome", "nome", "texto").obrigatorio(),
                    Campo.de("idade", "idade", "inteiro").obrigatorio(),
                    Campo.de("email", "email", "texto"),
                    Campo.de("username", "username", "texto"),
                    Campo.de("pais", "pais", "texto"),
                    Campo.de("cidade", "cidade", "texto"),
                    Campo.de("plano", "plano", "texto").comPadrao("gratuito"),
                    Campo.de("dataCadastro", "data_cadastro", "instante").comAutomatico("criacao"),
                    Campo.de("ultimoAcesso", "ultimo_acesso", "instante").comAutomatico("ambos"),
                    Campo.de("bio", "bio", "texto"),
                    Campo.de("idioma", "idioma", "texto").comPadrao("pt"),
                    Campo.de("tema", "tema", "texto").comPadrao("sistema"),
                    Campo.de("generosFavoritos", "generos_favoritos", "lista"),
                    Campo.de("avatarUrl", "avatar_url", "texto"),
                    Campo.de("preferencias", "preferencias", "json"),
                    Campo.de("historicoRecente", "historico_recente", "json").comPadrao(List.of())),
            List.of("nome"),
            List.of());

    public static final Recurso MUSICAS = new Recurso(
            "música",
            "musica",
            List.of(
                    Campo.de("id", "id", "id"),
                    Campo.de("nome", "nome", "texto").obrigatorio(),
                    Campo.de("artista", "artista", "texto").obrigatorio(),
                    Campo.de("album", "album", "texto"),
                    Campo.de("anoLancamento", "ano_lancamento", "inteiro"),
                    Campo.de("numeroFaixa", "numero_faixa", "inteiro"),
                    Campo.de("duracaoMs", "duracao_ms", "inteiro"),
                    Campo.de("genero", "genero", "texto"),
                    Campo.de("idioma", "idioma", "texto").comPadrao("pt"),
                    Campo.de("explicita", "explicita", "booleano"),
                    Campo.de("isrc", "isrc", "texto"),
                    Campo.de("gravadora", "gravadora", "texto"),
                    Campo.de("popularidade", "popularidade", "inteiro"),
                    Campo.de("letra", "letra", "texto"),
                    Campo.de("compositores", "compositores", "lista"),
                    Campo.de("produtores", "produtores", "lista"),
                    Campo.de("tags", "tags", "lista"),
                    Campo.de("audio", "audio", "json")),
            List.of("nome", "artista"),
            List.of());

    public static final Recurso PLAYLISTS = new RecursoPlaylist(
            "playlist",
            "playlist",
            List.of(
                    Campo.de("id", "id", "id"),
                    Campo.de("nome", "nome", "texto").obrigatorio(),
                    Campo.de("usuarioId", "usuario_id", "inteiro").obrigatorio(),
                    Campo.de("descricao", "descricao", "texto"),
                    Campo.de("publica", "publica", "booleano"),
                    Campo.de("colaborativa", "colaborativa", "booleano"),
                    Campo.de("criadaEm", "criada_em", "instante").comAutomatico("criacao"),
                    Campo.de("atualizadaEm", "atualizada_em", "instante").comAutomatico("ambos"),
                    Campo.de("capaUrl", "capa_url", "texto"),
                    Campo.de("tags", "tags", "lista")),
            List.of("nome"),
            List.of(
                    new Extra("totalMusicas",
                            "(SELECT count(*) FROM playlist_musica pm WHERE pm.playlist_id = t.id)",
                            "longo"),
                    new Extra("duracaoTotalMs",
                            "COALESCE((SELECT sum(m.duracao_ms) FROM playlist_musica pm "
                                    + "JOIN musica m ON m.id = pm.musica_id WHERE pm.playlist_id = t.id), 0)",
                            "longo"),
                    new Extra("musicaIds",
                            "ARRAY(SELECT pm.musica_id FROM playlist_musica pm "
                                    + "WHERE pm.playlist_id = t.id ORDER BY pm.posicao)",
                            "lista_int")));

    private Servicos() {
    }

    public static Pagina playlistsDoUsuario(int usuarioId, Integer pagina, Integer tamanho) {
        return PLAYLISTS.consultar("", "WHERE t.usuario_id = ?", List.of(usuarioId), "t.id", pagina, tamanho,
                new Recurso.Pai("usuario", "usuário", usuarioId));
    }

    public static Pagina musicasDaPlaylist(int playlistId, Integer pagina, Integer tamanho) {
        return MUSICAS.consultar("JOIN playlist_musica vinc ON vinc.musica_id = t.id",
                "WHERE vinc.playlist_id = ?", List.of(playlistId), "vinc.posicao", pagina, tamanho,
                new Recurso.Pai("playlist", "playlist", playlistId));
    }

    public static Pagina playlistsDaMusica(int musicaId, Integer pagina, Integer tamanho) {
        return PLAYLISTS.consultar("JOIN playlist_musica vinc ON vinc.playlist_id = t.id",
                "WHERE vinc.musica_id = ?", List.of(musicaId), "t.id", pagina, tamanho,
                new Recurso.Pai("musica", "música", musicaId));
    }
}