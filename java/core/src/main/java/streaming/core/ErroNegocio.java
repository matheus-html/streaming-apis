package streaming.core;

public abstract class ErroNegocio extends RuntimeException {

    protected ErroNegocio(String mensagem) {
        super(mensagem, null, false, false);
    }
}