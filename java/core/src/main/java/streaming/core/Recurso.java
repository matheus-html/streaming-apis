package streaming.core;

import java.sql.Array;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Types;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public class Recurso {

    public record Pai(String tabela, String nome, int id) {
    }

    private static final String FORMATO_INSTANTE = "YYYY-MM-DD\"T\"HH24:MI:SS\"Z\"";

    private static final Map<String, Object> PADROES = Map.of(
            "texto", "",
            "inteiro", 0,
            "booleano", false,
            "lista", List.of(),
            "json", Map.of());

    protected final String nome;
    protected final String tabela;
    protected final List<Campo> campos;
    protected final List<Extra> extras;
    private final List<String> colunasBusca;
    private final List<Campo> camposEditaveis;
    private final String selecao;

    public Recurso(String nome, String tabela, List<Campo> campos, List<String> colunasBusca, List<Extra> extras) {
        this.nome = nome;
        this.tabela = tabela;
        this.campos = campos;
        this.colunasBusca = colunasBusca;
        this.extras = extras;
        List<String> expressoes = new ArrayList<>();
        for (Campo campo : campos) {
            expressoes.add(expressao(campo));
        }
        for (Extra extra : extras) {
            expressoes.add(extra.sql() + " AS \"" + extra.api() + "\"");
        }
        this.selecao = String.join(", ", expressoes);
        this.camposEditaveis = campos.stream().filter(Campo::editavel).toList();
    }

    private static String expressao(Campo campo) {
        if (campo.tipo().equals("instante")) {
            return "to_char(t." + campo.coluna() + " AT TIME ZONE 'UTC', '" + FORMATO_INSTANTE
                    + "') AS \"" + campo.api() + "\"";
        }
        return "t." + campo.coluna() + " AS \"" + campo.api() + "\"";
    }

    static Integer comoInteiro(Object valor) {
        if (valor instanceof Integer inteiro) {
            return inteiro;
        }
        if (valor instanceof Long longo && longo >= Integer.MIN_VALUE && longo <= Integer.MAX_VALUE) {
            return longo.intValue();
        }
        return null;
    }

    private static void validar(Campo campo, Object valor) {
        boolean valido = switch (campo.tipo()) {
            case "texto" -> valor instanceof String;
            case "inteiro" -> comoInteiro(valor) != null;
            case "booleano" -> valor instanceof Boolean;
            case "lista" -> valor instanceof List<?> lista && lista.stream().allMatch(item -> item instanceof String);
            default -> valor instanceof Map<?, ?> || valor instanceof List<?>;
        };
        if (!valido) {
            throw new Invalido("campo '" + campo.api() + "' com tipo inválido");
        }
        if (campo.exigido() && campo.tipo().equals("texto") && ((String) valor).isBlank()) {
            throw new Invalido("campo '" + campo.api() + "' é obrigatório");
        }
    }

    public static int[] normalizar(Integer pagina, Integer tamanho) {
        int paginaFinal = pagina == null ? 1 : pagina;
        int tamanhoFinal = tamanho == null ? Config.TAMANHO_PADRAO : tamanho;
        if (paginaFinal < 1) {
            throw new Invalido("pagina deve ser um inteiro maior ou igual a 1");
        }
        if (tamanhoFinal < 1) {
            throw new Invalido("tamanho deve ser um inteiro maior ou igual a 1");
        }
        return new int[] {paginaFinal, Math.min(tamanhoFinal, Config.TAMANHO_MAXIMO)};
    }

    static String escaparLike(String termo) {
        return termo.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_");
    }

    private Object valorCriacao(Campo campo, Map<String, Object> dados) {
        if (dados.containsKey(campo.api())) {
            Object valor = dados.get(campo.api());
            validar(campo, valor);
            return valor;
        }
        if (campo.exigido()) {
            throw new Invalido("campo '" + campo.api() + "' é obrigatório");
        }
        return campo.padrao() != null ? campo.padrao() : PADROES.get(campo.tipo());
    }

    protected Map<String, Object> validarExtras(Map<String, Object> dados, boolean criando) {
        return Map.of();
    }

    protected void gravarExtras(Connection conexao, int identificador, Map<String, Object> extras)
            throws SQLException {
    }

    protected NaoEncontrado naoEncontrado(int identificador) {
        return new NaoEncontrado(nome + " " + identificador + " não encontrado");
    }

    private static Object lerValor(ResultSet resultado, int indice, String tipo) throws SQLException {
        switch (tipo) {
            case "id":
            case "inteiro":
                return resultado.getInt(indice);
            case "longo":
                return resultado.getLong(indice);
            case "booleano":
                return resultado.getBoolean(indice);
            case "lista":
                return lerTextos(resultado.getArray(indice));
            case "lista_int":
                return lerInteiros(resultado.getArray(indice));
            case "json":
                return Json.ler(resultado.getString(indice));
            default:
                return resultado.getString(indice);
        }
    }

    private static List<String> lerTextos(Array vetor) throws SQLException {
        Object[] itens = (Object[]) vetor.getArray();
        List<String> textos = new ArrayList<>(itens.length);
        for (Object item : itens) {
            textos.add((String) item);
        }
        return textos;
    }

    private static List<Integer> lerInteiros(Array vetor) throws SQLException {
        Object[] itens = (Object[]) vetor.getArray();
        List<Integer> inteiros = new ArrayList<>(itens.length);
        for (Object item : itens) {
            inteiros.add(((Number) item).intValue());
        }
        return inteiros;
    }

    private Map<String, Object> ler(ResultSet resultado) throws SQLException {
        Map<String, Object> linha = new LinkedHashMap<>();
        int indice = 1;
        for (Campo campo : campos) {
            linha.put(campo.api(), lerValor(resultado, indice++, campo.tipo()));
        }
        for (Extra extra : extras) {
            linha.put(extra.api(), lerValor(resultado, indice++, extra.tipo()));
        }
        return linha;
    }

    private Map<String, Object> buscar(Connection conexao, int identificador) throws SQLException {
        try (PreparedStatement comando = conexao.prepareStatement(
                "SELECT " + selecao + " FROM " + tabela + " t WHERE t.id = ?")) {
            comando.setInt(1, identificador);
            try (ResultSet resultado = comando.executeQuery()) {
                return resultado.next() ? ler(resultado) : null;
            }
        }
    }

    private static int ligar(PreparedStatement comando, List<?> parametros, int inicio) throws SQLException {
        int indice = inicio;
        for (Object parametro : parametros) {
            comando.setObject(indice++, parametro);
        }
        return indice;
    }

    private static void ligarCampos(Connection conexao, PreparedStatement comando, List<Campo> alvos,
            List<Object> valores) throws SQLException {
        for (int i = 0; i < valores.size(); i++) {
            Campo campo = alvos.get(i);
            Object valor = valores.get(i);
            int indice = i + 1;
            if (campo == null) {
                comando.setObject(indice, valor);
                continue;
            }
            switch (campo.tipo()) {
                case "texto" -> comando.setString(indice, (String) valor);
                case "inteiro" -> comando.setInt(indice, comoInteiro(valor));
                case "booleano" -> comando.setBoolean(indice, (Boolean) valor);
                case "lista" -> comando.setArray(indice,
                        conexao.createArrayOf("text", ((List<?>) valor).toArray(new String[0])));
                default -> comando.setObject(indice, Json.escrever(valor), Types.OTHER);
            }
        }
    }

    private static RuntimeException traduzir(SQLException erro) {
        String estado = erro.getSQLState();
        if ("23503".equals(estado)) {
            return new Invalido("referência inexistente");
        }
        if ("23514".equals(estado)) {
            return new Invalido("valor fora do intervalo permitido");
        }
        return new IllegalStateException(erro);
    }

    public Pagina consultar(String juncao, String filtro, List<?> parametros, String ordem, Integer pagina,
            Integer tamanho, Pai pai) {
        int[] normalizados = normalizar(pagina, tamanho);
        int paginaAtual = normalizados[0];
        int tamanhoAtual = normalizados[1];
        String base = "FROM " + tabela + " t " + juncao + " " + filtro;
        try (Connection conexao = Banco.fonte().getConnection()) {
            if (pai != null) {
                try (PreparedStatement comando = conexao.prepareStatement(
                        "SELECT 1 FROM " + pai.tabela() + " WHERE id = ?")) {
                    comando.setInt(1, pai.id());
                    try (ResultSet resultado = comando.executeQuery()) {
                        if (!resultado.next()) {
                            throw new NaoEncontrado(pai.nome() + " " + pai.id() + " não encontrado");
                        }
                    }
                }
            }
            long total;
            try (PreparedStatement comando = conexao.prepareStatement("SELECT count(*) AS total " + base)) {
                ligar(comando, parametros, 1);
                try (ResultSet resultado = comando.executeQuery()) {
                    resultado.next();
                    total = resultado.getLong(1);
                }
            }
            List<Map<String, Object>> itens = new ArrayList<>();
            try (PreparedStatement comando = conexao.prepareStatement(
                    "SELECT " + selecao + " " + base + " ORDER BY " + ordem + " LIMIT ? OFFSET ?")) {
                int proximo = ligar(comando, parametros, 1);
                comando.setInt(proximo, tamanhoAtual);
                comando.setLong(proximo + 1, (long) (paginaAtual - 1) * tamanhoAtual);
                try (ResultSet resultado = comando.executeQuery()) {
                    while (resultado.next()) {
                        itens.add(ler(resultado));
                    }
                }
            }
            return new Pagina(itens, paginaAtual, tamanhoAtual, total);
        } catch (SQLException erro) {
            throw new IllegalStateException(erro);
        }
    }

    public Pagina listar(Integer pagina, Integer tamanho, String termo) {
        String filtro = "";
        List<Object> parametros = new ArrayList<>();
        if (termo != null && !termo.isEmpty()) {
            String padrao = "%" + escaparLike(termo) + "%";
            StringBuilder condicao = new StringBuilder("WHERE ");
            for (int i = 0; i < colunasBusca.size(); i++) {
                if (i > 0) {
                    condicao.append(" OR ");
                }
                condicao.append("t.").append(colunasBusca.get(i)).append(" ILIKE ?");
                parametros.add(padrao);
            }
            filtro = condicao.toString();
        }
        return consultar("", filtro, parametros, "t.id", pagina, tamanho, null);
    }

    public Map<String, Object> obter(int identificador) {
        try (Connection conexao = Banco.fonte().getConnection()) {
            Map<String, Object> linha = buscar(conexao, identificador);
            if (linha == null) {
                throw naoEncontrado(identificador);
            }
            return linha;
        } catch (SQLException erro) {
            throw new IllegalStateException(erro);
        }
    }

    public Map<String, Object> criar(Map<String, Object> dados) {
        if (dados == null) {
            throw new Invalido("o corpo deve ser um objeto");
        }
        List<String> colunas = new ArrayList<>();
        List<String> marcadores = new ArrayList<>();
        List<Campo> alvos = new ArrayList<>();
        List<Object> valores = new ArrayList<>();
        for (Campo campo : campos) {
            if (campo.tipo().equals("id")) {
                continue;
            }
            if (campo.tipo().equals("instante")) {
                if (!campo.automatico().isEmpty()) {
                    colunas.add(campo.coluna());
                    marcadores.add("now()");
                }
                continue;
            }
            Object valor = valorCriacao(campo, dados);
            colunas.add(campo.coluna());
            marcadores.add("?");
            alvos.add(campo);
            valores.add(valor);
        }
        Map<String, Object> gravacao = validarExtras(dados, true);
        String sql = "INSERT INTO " + tabela + " (" + String.join(", ", colunas) + ") VALUES ("
                + String.join(", ", marcadores) + ") RETURNING id";
        try (Connection conexao = Banco.fonte().getConnection()) {
            conexao.setAutoCommit(false);
            try {
                int identificador;
                try (PreparedStatement comando = conexao.prepareStatement(sql)) {
                    ligarCampos(conexao, comando, alvos, valores);
                    try (ResultSet resultado = comando.executeQuery()) {
                        resultado.next();
                        identificador = resultado.getInt(1);
                    }
                }
                gravarExtras(conexao, identificador, gravacao);
                Map<String, Object> linha = buscar(conexao, identificador);
                conexao.commit();
                return linha;
            } catch (SQLException | RuntimeException erro) {
                conexao.rollback();
                throw erro;
            } finally {
                conexao.setAutoCommit(true);
            }
        } catch (SQLException erro) {
            throw traduzir(erro);
        }
    }

    public Map<String, Object> atualizar(int identificador, Map<String, Object> dados) {
        if (dados == null) {
            throw new Invalido("o corpo deve ser um objeto");
        }
        List<String> atribuicoes = new ArrayList<>();
        List<Campo> alvos = new ArrayList<>();
        List<Object> valores = new ArrayList<>();
        for (Campo campo : camposEditaveis) {
            if (dados.containsKey(campo.api())) {
                Object valor = dados.get(campo.api());
                validar(campo, valor);
                atribuicoes.add(campo.coluna() + " = ?");
                alvos.add(campo);
                valores.add(valor);
            }
        }
        for (Campo campo : campos) {
            if (campo.tipo().equals("instante") && campo.automatico().equals("ambos")) {
                atribuicoes.add(campo.coluna() + " = now()");
            }
        }
        Map<String, Object> gravacao = validarExtras(dados, false);
        String sql = atribuicoes.isEmpty()
                ? "SELECT id FROM " + tabela + " WHERE id = ?"
                : "UPDATE " + tabela + " SET " + String.join(", ", atribuicoes) + " WHERE id = ? RETURNING id";
        alvos.add(null);
        valores.add(identificador);
        try (Connection conexao = Banco.fonte().getConnection()) {
            conexao.setAutoCommit(false);
            try {
                try (PreparedStatement comando = conexao.prepareStatement(sql)) {
                    ligarCampos(conexao, comando, alvos, valores);
                    try (ResultSet resultado = comando.executeQuery()) {
                        if (!resultado.next()) {
                            throw naoEncontrado(identificador);
                        }
                    }
                }
                gravarExtras(conexao, identificador, gravacao);
                Map<String, Object> linha = buscar(conexao, identificador);
                conexao.commit();
                return linha;
            } catch (SQLException | RuntimeException erro) {
                conexao.rollback();
                throw erro;
            } finally {
                conexao.setAutoCommit(true);
            }
        } catch (SQLException erro) {
            throw traduzir(erro);
        }
    }

    public void remover(int identificador) {
        try (Connection conexao = Banco.fonte().getConnection();
                PreparedStatement comando = conexao.prepareStatement(
                        "DELETE FROM " + tabela + " WHERE id = ? RETURNING id")) {
            comando.setInt(1, identificador);
            try (ResultSet resultado = comando.executeQuery()) {
                if (!resultado.next()) {
                    throw naoEncontrado(identificador);
                }
            }
        } catch (SQLException erro) {
            if ("23503".equals(erro.getSQLState())) {
                throw new Conflito(nome + " " + identificador + " está em uso e não pode ser removido");
            }
            throw new IllegalStateException(erro);
        }
    }
}