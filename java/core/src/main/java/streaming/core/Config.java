package streaming.core;

public final class Config {

    public static final String DB_HOST = ambiente("DB_HOST", "localhost");
    public static final int DB_PORT = Integer.parseInt(ambiente("DB_PORT", "5432"));
    public static final String DB_NAME = ambiente("DB_NAME", "streaming");
    public static final String DB_USER = ambiente("DB_USER", "streaming");
    public static final String DB_PASSWORD = ambiente("DB_PASSWORD", "streaming");
    public static final int POOL_SIZE = Integer.parseInt(ambiente("POOL_SIZE", "32"));
    public static final int PORT = Integer.parseInt(ambiente("PORT", "8080"));

    public static final int TAMANHO_PADRAO = 20;
    public static final int TAMANHO_MAXIMO = 200;

    private Config() {
    }

    private static String ambiente(String nome, String padrao) {
        String valor = System.getenv(nome);
        return valor == null || valor.isBlank() ? padrao : valor;
    }
}