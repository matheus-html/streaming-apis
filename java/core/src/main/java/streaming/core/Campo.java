package streaming.core;

public record Campo(String api, String coluna, String tipo, boolean exigido, Object padrao, String automatico) {

    public static Campo de(String api, String coluna, String tipo) {
        return new Campo(api, coluna, tipo, false, null, "");
    }

    public Campo obrigatorio() {
        return new Campo(api, coluna, tipo, true, padrao, automatico);
    }

    public Campo comPadrao(Object valor) {
        return new Campo(api, coluna, tipo, exigido, valor, automatico);
    }

    public Campo comAutomatico(String modo) {
        return new Campo(api, coluna, tipo, exigido, padrao, modo);
    }

    public boolean editavel() {
        return !tipo.equals("id") && !tipo.equals("instante");
    }
}