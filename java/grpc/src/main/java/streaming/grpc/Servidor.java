package streaming.grpc;

import io.grpc.Server;
import io.grpc.ServerBuilder;
import io.grpc.protobuf.services.ProtoReflectionService;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import streaming.core.Banco;
import streaming.core.Config;

public final class Servidor {

    private Servidor() {
    }

    public static void main(String[] argumentos) throws Exception {
        Banco.fonte();
        int threads = Integer.parseInt(System.getenv().getOrDefault("GRPC_THREADS", "80"));
        ExecutorService executor = Executors.newFixedThreadPool(threads);
        Server servidor = ServerBuilder.forPort(Config.PORT)
                .executor(executor)
                .addService(new UsuarioServico())
                .addService(new MusicaServico())
                .addService(new PlaylistServico())
                .addService(ProtoReflectionService.newInstance())
                .build()
                .start();
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            servidor.shutdown();
            executor.shutdown();
        }));
        servidor.awaitTermination();
    }
}