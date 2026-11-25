package streaming.core;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;

public class RecursoPlaylist extends Recurso {

    public RecursoPlaylist(String nome, String tabela, List<Campo> campos, List<String> colunasBusca,
            List<Extra> extras) {
        super(nome, tabela, campos, colunasBusca, extras);
    }

    @Override
    protected Map<String, Object> validarExtras(Map<String, Object> dados, boolean criando) {
        if (!dados.containsKey("musicaIds")) {
            if (criando) {
                throw new Invalido("campo 'musicaIds' é obrigatório");
            }
            return Map.of();
        }
        Object valor = dados.get("musicaIds");
        if (!(valor instanceof List<?> lista) || lista.isEmpty()) {
            throw new Invalido("musicaIds deve ser uma lista não vazia de inteiros");
        }
        List<Integer> identificadores = new ArrayList<>(lista.size());
        for (Object item : lista) {
            Integer inteiro = comoInteiro(item);
            if (inteiro == null) {
                throw new Invalido("musicaIds deve ser uma lista não vazia de inteiros");
            }
            identificadores.add(inteiro);
        }
        if (new HashSet<>(identificadores).size() != identificadores.size()) {
            throw new Invalido("musicaIds não pode ter itens repetidos");
        }
        Map<String, Object> extras = new HashMap<>();
        extras.put("musicaIds", identificadores);
        return extras;
    }

    @Override
    protected void gravarExtras(Connection conexao, int identificador, Map<String, Object> extras)
            throws SQLException {
        Object valor = extras.get("musicaIds");
        if (valor == null) {
            return;
        }
        try (PreparedStatement comando = conexao.prepareStatement(
                "DELETE FROM playlist_musica WHERE playlist_id = ?")) {
            comando.setInt(1, identificador);
            comando.executeUpdate();
        }
        try (PreparedStatement comando = conexao.prepareStatement(
                "INSERT INTO playlist_musica (playlist_id, musica_id, posicao) VALUES (?, ?, ?)")) {
            int posicao = 1;
            for (Object musicaId : (List<?>) valor) {
                comando.setInt(1, identificador);
                comando.setInt(2, (Integer) musicaId);
                comando.setInt(3, posicao++);
                comando.addBatch();
            }
            comando.executeBatch();
        }
    }
}