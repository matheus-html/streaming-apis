package streaming.core;

import com.zaxxer.hikari.HikariConfig;
import com.zaxxer.hikari.HikariDataSource;
import javax.sql.DataSource;

public final class Banco {

    private static volatile DataSource fonte;

    private Banco() {
    }

    public static DataSource fonte() {
        DataSource atual = fonte;
        if (atual == null) {
            synchronized (Banco.class) {
                if (fonte == null) {
                    fonte = criar();
                }
                atual = fonte;
            }
        }
        return atual;
    }

    private static DataSource criar() {
        HikariConfig configuracao = new HikariConfig();
        configuracao.setJdbcUrl("jdbc:postgresql://" + Config.DB_HOST + ":" + Config.DB_PORT + "/"
                + Config.DB_NAME + "?reWriteBatchedInserts=true");
        configuracao.setUsername(Config.DB_USER);
        configuracao.setPassword(Config.DB_PASSWORD);
        configuracao.setMaximumPoolSize(Config.POOL_SIZE);
        configuracao.setMinimumIdle(Config.POOL_SIZE);
        configuracao.setConnectionTimeout(10000);
        configuracao.setInitializationFailTimeout(30000);
        configuracao.setAutoCommit(true);
        configuracao.setPoolName("streaming");
        return new HikariDataSource(configuracao);
    }
}