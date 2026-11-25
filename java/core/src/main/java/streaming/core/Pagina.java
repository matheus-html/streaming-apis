package streaming.core;

import java.util.List;
import java.util.Map;

public record Pagina(List<Map<String, Object>> itens, int pagina, int tamanho, long total) {
}