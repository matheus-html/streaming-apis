import anyio.to_thread
from fastapi import FastAPI, Request, Response

from .contrato import gerar_wsdl
from .mensagens import processar

app = FastAPI(title="Streaming - SOAP (Python)", docs_url=None, redoc_url=None, openapi_url=None)

TIPO_XML = "text/xml; charset=utf-8"


@app.post("/soap")
async def chamar(requisicao: Request):
    corpo = await requisicao.body()
    status, resposta = await anyio.to_thread.run_sync(processar, corpo)
    return Response(content=resposta, status_code=status, media_type=TIPO_XML)


@app.get("/soap")
def wsdl(requisicao: Request):
    endereco = str(requisicao.url).split("?")[0]
    return Response(content=gerar_wsdl(endereco), media_type=TIPO_XML)


@app.get("/saude")
def saude():
    return {"status": "ok"}