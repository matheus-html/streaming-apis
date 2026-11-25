package streaming.rest;

import java.util.Map;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;
import streaming.core.Conflito;
import streaming.core.Invalido;
import streaming.core.NaoEncontrado;

@RestControllerAdvice
public class Erros {

    private static ResponseEntity<Map<String, String>> resposta(HttpStatus status, String mensagem) {
        return ResponseEntity.status(status).body(Map.of("erro", mensagem));
    }

    @ExceptionHandler(NaoEncontrado.class)
    public ResponseEntity<Map<String, String>> naoEncontrado(NaoEncontrado erro) {
        return resposta(HttpStatus.NOT_FOUND, erro.getMessage());
    }

    @ExceptionHandler(Invalido.class)
    public ResponseEntity<Map<String, String>> invalido(Invalido erro) {
        return resposta(HttpStatus.BAD_REQUEST, erro.getMessage());
    }

    @ExceptionHandler(Conflito.class)
    public ResponseEntity<Map<String, String>> conflito(Conflito erro) {
        return resposta(HttpStatus.CONFLICT, erro.getMessage());
    }

    @ExceptionHandler({HttpMessageNotReadableException.class, MethodArgumentTypeMismatchException.class})
    public ResponseEntity<Map<String, String>> requisicaoInvalida(Exception erro) {
        return resposta(HttpStatus.BAD_REQUEST, "requisição inválida");
    }
}