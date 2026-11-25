package streaming.rest;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import streaming.core.Pagina;
import streaming.core.Servicos;

@RestController
@RequestMapping("/usuarios")
public class UsuariosController extends CrudController {

    public UsuariosController() {
        super(Servicos.USUARIOS);
    }

    @GetMapping("/{id}/playlists")
    public Pagina playlists(
            @PathVariable("id") int id,
            @RequestParam(name = "pagina", required = false) Integer pagina,
            @RequestParam(name = "tamanho", required = false) Integer tamanho) {
        return Servicos.playlistsDoUsuario(id, pagina, tamanho);
    }
}