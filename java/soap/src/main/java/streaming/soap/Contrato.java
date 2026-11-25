package streaming.soap;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public final class Contrato {

    public static final String NS = "urn:streaming";

    public record Elemento(String nome, String tipo) {
    }

    public record Operacao(List<Elemento> requisicao, String[] resposta) {
    }

    public record Recurso(String tipo, String plural, String nome) {
    }

    public static final Map<String, List<Elemento>> TIPOS = new LinkedHashMap<>();
    public static final List<Recurso> RECURSOS = List.of(
            new Recurso("Usuario", "Usuarios", "usuario"),
            new Recurso("Musica", "Musicas", "musica"),
            new Recurso("Playlist", "Playlists", "playlist"));
    public static final Map<String, Operacao> OPERACOES = new LinkedHashMap<>();

    private static final List<Elemento> PAGINACAO = List.of(new Elemento("pagina", "inteiro?"),
            new Elemento("tamanho", "inteiro?"));

    static {
        TIPOS.put("Preferencias", List.of(
                e("notificacoes", "booleano"), e("qualidadeAudio", "texto"), e("conteudoExplicito", "booleano"),
                e("crossfadeSegundos", "inteiro"), e("modoOffline", "booleano")));
        TIPOS.put("HistoricoItem", List.of(
                e("musicaId", "inteiro"), e("iniciadaEm", "texto"), e("duracaoOuvidaMs", "inteiro"),
                e("dispositivo", "texto")));
        TIPOS.put("Audio", List.of(
                e("bpm", "inteiro"), e("tonalidade", "texto"), e("energia", "decimal"),
                e("dancabilidade", "decimal"), e("valencia", "decimal"), e("acustica", "decimal")));
        TIPOS.put("Usuario", List.of(
                e("id", "inteiro"), e("nome", "texto"), e("idade", "inteiro"), e("email", "texto"),
                e("username", "texto"), e("pais", "texto"), e("cidade", "texto"), e("plano", "texto"),
                e("dataCadastro", "texto"), e("ultimoAcesso", "texto"), e("bio", "texto"),
                e("idioma", "texto"), e("tema", "texto"), e("generosFavoritos", "lista_texto"),
                e("avatarUrl", "texto"), e("preferencias", "obj:Preferencias"),
                e("historicoRecente", "lista:HistoricoItem")));
        TIPOS.put("Musica", List.of(
                e("id", "inteiro"), e("nome", "texto"), e("artista", "texto"), e("album", "texto"),
                e("anoLancamento", "inteiro"), e("numeroFaixa", "inteiro"), e("duracaoMs", "inteiro"),
                e("genero", "texto"), e("idioma", "texto"), e("explicita", "booleano"), e("isrc", "texto"),
                e("gravadora", "texto"), e("popularidade", "inteiro"), e("letra", "texto"),
                e("compositores", "lista_texto"), e("produtores", "lista_texto"), e("tags", "lista_texto"),
                e("audio", "obj:Audio")));
        TIPOS.put("Playlist", List.of(
                e("id", "inteiro"), e("nome", "texto"), e("usuarioId", "inteiro"), e("descricao", "texto"),
                e("publica", "booleano"), e("colaborativa", "booleano"), e("criadaEm", "texto"),
                e("atualizadaEm", "texto"), e("capaUrl", "texto"), e("tags", "lista_texto"),
                e("totalMusicas", "longo"), e("duracaoTotalMs", "longo"), e("musicaIds", "lista_int")));

        for (Recurso recurso : RECURSOS) {
            String tipo = recurso.tipo();
            String nome = recurso.nome();
            List<Elemento> listagem = new ArrayList<>(PAGINACAO);
            listagem.add(e("nome", "texto?"));
            OPERACOES.put("Listar" + recurso.plural(), new Operacao(listagem, new String[] {"pagina", nome, tipo}));
            OPERACOES.put("Obter" + tipo, new Operacao(List.of(e("id", "inteiro")),
                    new String[] {"entidade", nome, tipo}));
            OPERACOES.put("Criar" + tipo, new Operacao(List.of(e(nome, "obj:" + tipo)),
                    new String[] {"entidade", nome, tipo}));
            OPERACOES.put("Atualizar" + tipo, new Operacao(List.of(e("id", "inteiro"), e(nome, "obj:" + tipo)),
                    new String[] {"entidade", nome, tipo}));
            OPERACOES.put("Remover" + tipo, new Operacao(List.of(e("id", "inteiro")), new String[] {"vazio"}));
        }
        OPERACOES.put("ListarPlaylistsDoUsuario", relacional("playlist", "Playlist"));
        OPERACOES.put("ListarMusicasDaPlaylist", relacional("musica", "Musica"));
        OPERACOES.put("ListarPlaylistsDaMusica", relacional("playlist", "Playlist"));
    }

    private Contrato() {
    }

    private static Elemento e(String nome, String tipo) {
        return new Elemento(nome, tipo);
    }

    private static Operacao relacional(String nome, String tipo) {
        List<Elemento> requisicao = new ArrayList<>();
        requisicao.add(e("id", "inteiro"));
        requisicao.addAll(PAGINACAO);
        return new Operacao(requisicao, new String[] {"pagina", nome, tipo});
    }
}