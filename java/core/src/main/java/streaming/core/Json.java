package streaming.core;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;

public final class Json {

    private static final ObjectMapper MAPEADOR = new ObjectMapper();

    private Json() {
    }

    public static Object ler(String texto) {
        try {
            return MAPEADOR.readValue(texto, Object.class);
        } catch (JsonProcessingException erro) {
            throw new IllegalStateException(erro);
        }
    }

    public static String escrever(Object valor) {
        try {
            return MAPEADOR.writeValueAsString(valor);
        } catch (JsonProcessingException erro) {
            throw new IllegalStateException(erro);
        }
    }
}