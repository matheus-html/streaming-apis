package streaming.soap;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import streaming.core.Banco;

@SpringBootApplication
public class Aplicacao {

    public static void main(String[] argumentos) {
        Banco.fonte();
        SpringApplication.run(Aplicacao.class, argumentos);
    }
}