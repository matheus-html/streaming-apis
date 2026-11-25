package streaming.gql;

import graphql.schema.DataFetchingEnvironment;
import java.util.LinkedHashMap;
import java.util.Map;
import org.springframework.graphql.data.method.annotation.Argument;
import org.springframework.graphql.data.method.annotation.MutationMapping;
import org.springframework.graphql.data.method.annotation.QueryMapping;
import org.springframework.stereotype.Controller;
import streaming.core.Pagina;
import streaming.core.Servicos;

@Controller
public class ApiController {

    private static Map<String, Object> pagina(Pagina origem) {
        Map<String, Object> resultado = new LinkedHashMap<>();
        resultado.put("itens", origem.itens());
        resultado.put("pagina", origem.pagina());
        resultado.put("tamanho", origem.tamanho());
        resultado.put("total", origem.total());
        return resultado;
    }

    private static Map<String, Object> entrada(DataFetchingEnvironment ambiente) {
        return ambiente.getArgument("entrada");
    }

    @QueryMapping
    public Map<String, Object> usuarios(@Argument Integer pagina, @Argument Integer tamanho,
            @Argument String nome) {
        return pagina(Servicos.USUARIOS.listar(pagina, tamanho, nome));
    }

    @QueryMapping
    public Map<String, Object> usuario(@Argument int id) {
        return Servicos.USUARIOS.obter(id);
    }

    @QueryMapping
    public Map<String, Object> musicas(@Argument Integer pagina, @Argument Integer tamanho,
            @Argument String nome) {
        return pagina(Servicos.MUSICAS.listar(pagina, tamanho, nome));
    }

    @QueryMapping
    public Map<String, Object> musica(@Argument int id) {
        return Servicos.MUSICAS.obter(id);
    }

    @QueryMapping
    public Map<String, Object> playlists(@Argument Integer pagina, @Argument Integer tamanho,
            @Argument String nome) {
        return pagina(Servicos.PLAYLISTS.listar(pagina, tamanho, nome));
    }

    @QueryMapping
    public Map<String, Object> playlist(@Argument int id) {
        return Servicos.PLAYLISTS.obter(id);
    }

    @QueryMapping
    public Map<String, Object> playlistsDoUsuario(@Argument int usuarioId, @Argument Integer pagina,
            @Argument Integer tamanho) {
        return pagina(Servicos.playlistsDoUsuario(usuarioId, pagina, tamanho));
    }

    @QueryMapping
    public Map<String, Object> musicasDaPlaylist(@Argument int playlistId, @Argument Integer pagina,
            @Argument Integer tamanho) {
        return pagina(Servicos.musicasDaPlaylist(playlistId, pagina, tamanho));
    }

    @QueryMapping
    public Map<String, Object> playlistsDaMusica(@Argument int musicaId, @Argument Integer pagina,
            @Argument Integer tamanho) {
        return pagina(Servicos.playlistsDaMusica(musicaId, pagina, tamanho));
    }

    @MutationMapping
    public Map<String, Object> criarUsuario(DataFetchingEnvironment ambiente) {
        return Servicos.USUARIOS.criar(entrada(ambiente));
    }

    @MutationMapping
    public Map<String, Object> atualizarUsuario(@Argument int id, DataFetchingEnvironment ambiente) {
        return Servicos.USUARIOS.atualizar(id, entrada(ambiente));
    }

    @MutationMapping
    public boolean removerUsuario(@Argument int id) {
        Servicos.USUARIOS.remover(id);
        return true;
    }

    @MutationMapping
    public Map<String, Object> criarMusica(DataFetchingEnvironment ambiente) {
        return Servicos.MUSICAS.criar(entrada(ambiente));
    }

    @MutationMapping
    public Map<String, Object> atualizarMusica(@Argument int id, DataFetchingEnvironment ambiente) {
        return Servicos.MUSICAS.atualizar(id, entrada(ambiente));
    }

    @MutationMapping
    public boolean removerMusica(@Argument int id) {
        Servicos.MUSICAS.remover(id);
        return true;
    }

    @MutationMapping
    public Map<String, Object> criarPlaylist(DataFetchingEnvironment ambiente) {
        return Servicos.PLAYLISTS.criar(entrada(ambiente));
    }

    @MutationMapping
    public Map<String, Object> atualizarPlaylist(@Argument int id, DataFetchingEnvironment ambiente) {
        return Servicos.PLAYLISTS.atualizar(id, entrada(ambiente));
    }

    @MutationMapping
    public boolean removerPlaylist(@Argument int id) {
        Servicos.PLAYLISTS.remover(id);
        return true;
    }
}