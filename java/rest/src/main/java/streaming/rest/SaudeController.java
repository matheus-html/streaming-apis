package streaming.rest;

import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class SaudeController {

    @GetMapping("/saude")
    public Map<String, String> saude() {
        return Map.of("status", "ok");
    }
}