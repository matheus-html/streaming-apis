package streaming.rest;

import java.util.Map;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import streaming.core.Pagina;
import streaming.core.Recurso;

public abstract class CrudController {

    private final Recurso recurso;

    protected CrudController(Recurso recurso) {
        this.recurso = recurso;
    }

    @GetMapping
    public Pagina listar(
            @RequestParam(name = "pagina", required = false) Integer pagina,
            @RequestParam(name = "tamanho", required = false) Integer tamanho,
            @RequestParam(name = "nome", required = false) String nome) {
        return recurso.listar(pagina, tamanho, nome);
    }

    @GetMapping("/{id}")
    public Map<String, Object> obter(@PathVariable("id") int id) {
        return recurso.obter(id);
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public Map<String, Object> criar(@RequestBody Map<String, Object> corpo) {
        return recurso.criar(corpo);
    }

    @PutMapping("/{id}")
    public Map<String, Object> atualizar(@PathVariable("id") int id, @RequestBody Map<String, Object> corpo) {
        return recurso.atualizar(id, corpo);
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void remover(@PathVariable("id") int id) {
        recurso.remover(id);
    }
}