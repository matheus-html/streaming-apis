package streaming.soap;

import jakarta.servlet.http.HttpServletRequest;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.Map;
import org.springframework.core.io.ClassPathResource;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class SoapController {

    private static final MediaType XML = MediaType.parseMediaType("text/xml;charset=UTF-8");

    private final String wsdl;

    public SoapController() throws IOException {
        try (var entrada = new ClassPathResource("streaming.wsdl").getInputStream()) {
            this.wsdl = new String(entrada.readAllBytes(), StandardCharsets.UTF_8);
        }
    }

    @PostMapping("/soap")
    public ResponseEntity<byte[]> chamar(@RequestBody byte[] corpo) {
        Mensagens.Resposta resposta = Mensagens.processar(corpo);
        return ResponseEntity.status(resposta.status()).contentType(XML).body(resposta.corpo());
    }

    @GetMapping("/soap")
    public ResponseEntity<String> descrever(HttpServletRequest requisicao) {
        String endereco = requisicao.getRequestURL().toString();
        return ResponseEntity.ok().contentType(XML).body(wsdl.replace("__ENDERECO__", endereco));
    }

    @GetMapping("/saude")
    public Map<String, String> saude() {
        return Map.of("status", "ok");
    }
}