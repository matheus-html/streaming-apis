from fastapi import APIRouter, Body, FastAPI, Query, Response
from fastapi.responses import JSONResponse

from core import servicos
from core.erros import Conflito, Invalido, NaoEncontrado

app = FastAPI(title="Streaming - REST (Python)")


@app.exception_handler(NaoEncontrado)
async def tratar_nao_encontrado(requisicao, erro):
    return JSONResponse({"erro": str(erro)}, status_code=404)


@app.exception_handler(Invalido)
async def tratar_invalido(requisicao, erro):
    return JSONResponse({"erro": str(erro)}, status_code=400)


@app.exception_handler(Conflito)
async def tratar_conflito(requisicao, erro):
    return JSONResponse({"erro": str(erro)}, status_code=409)


def rotas_crud(prefixo, recurso):
    roteador = APIRouter(prefix=prefixo, tags=[prefixo.strip("/")])

    @roteador.get("")
    def listar(
        pagina: int | None = Query(None),
        tamanho: int | None = Query(None),
        nome: str | None = Query(None),
    ):
        return JSONResponse(recurso.listar(pagina, tamanho, nome))

    @roteador.get("/{identificador}")
    def obter(identificador: int):
        return JSONResponse(recurso.obter(identificador))

    @roteador.post("", status_code=201)
    def criar(corpo: dict = Body(...)):
        return JSONResponse(recurso.criar(corpo), status_code=201)

    @roteador.put("/{identificador}")
    def atualizar(identificador: int, corpo: dict = Body(...)):
        return JSONResponse(recurso.atualizar(identificador, corpo))

    @roteador.delete("/{identificador}", status_code=204)
    def remover(identificador: int):
        recurso.remover(identificador)
        return Response(status_code=204)

    return roteador


app.include_router(rotas_crud("/usuarios", servicos.usuarios))
app.include_router(rotas_crud("/musicas", servicos.musicas))
app.include_router(rotas_crud("/playlists", servicos.playlists))


@app.get("/usuarios/{identificador}/playlists", tags=["usuarios"])
def playlists_do_usuario(
    identificador: int, pagina: int | None = Query(None), tamanho: int | None = Query(None)
):
    return JSONResponse(servicos.playlists_do_usuario(identificador, pagina, tamanho))


@app.get("/playlists/{identificador}/musicas", tags=["playlists"])
def musicas_da_playlist(
    identificador: int, pagina: int | None = Query(None), tamanho: int | None = Query(None)
):
    return JSONResponse(servicos.musicas_da_playlist(identificador, pagina, tamanho))


@app.get("/musicas/{identificador}/playlists", tags=["musicas"])
def playlists_da_musica(
    identificador: int, pagina: int | None = Query(None), tamanho: int | None = Query(None)
):
    return JSONResponse(servicos.playlists_da_musica(identificador, pagina, tamanho))


@app.get("/saude")
def saude():
    return {"status": "ok"}