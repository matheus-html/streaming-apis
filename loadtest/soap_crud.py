import re
from xml.sax.saxutils import escape

from locust import HttpUser, constant

from comum import TIMEOUT
from crud_comum import CicloBase

NS = "urn:streaming"
CABECALHO = {"Content-Type": "text/xml; charset=utf-8"}
NOMES = {"usuario": "Usuario", "musica": "Musica", "playlist": "Playlist"}
RELACIONADOS = {
    "playlists_do_usuario": "ListarPlaylistsDoUsuario",
    "musicas_da_playlist": "ListarMusicasDaPlaylist",
    "playlists_da_musica": "ListarPlaylistsDaMusica",
}
ENVELOPE = (
    '<?xml version="1.0" encoding="utf-8"?>'
    '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tns="urn:streaming">'
    "<soapenv:Body><tns:{operacao}>{corpo}</tns:{operacao}></soapenv:Body></soapenv:Envelope>"
)
PADRAO_ID = re.compile(rb"<(?:\w+:)?id>(\d+)</")


def valor_xml(valor):
    if isinstance(valor, bool):
        return "true" if valor else "false"
    return escape(str(valor))


def elemento(nome, valor):
    if isinstance(valor, dict):
        interno = "".join(elemento(k, v) for k, v in valor.items())
    elif isinstance(valor, list):
        interno = "".join(elemento("item", item) for item in valor)
    else:
        interno = valor_xml(valor)
    return f"<tns:{nome}>{interno}</tns:{nome}>"


class CicloSoap(CicloBase):
    def chamar(self, nome, operacao, corpo):
        with self.client.post(
            "/soap",
            data=ENVELOPE.format(operacao=operacao, corpo=corpo).encode("utf-8"),
            headers={**CABECALHO, "SOAPAction": f'"{NS}/{operacao}"'},
            name=nome,
            timeout=TIMEOUT,
            catch_response=True,
        ) as resposta:
            if resposta.status_code != 200:
                resposta.failure(f"http {resposta.status_code}")
                return None
            if b"Fault" in resposta.content[:400]:
                resposta.failure("soap fault")
                return None
            resposta.success()
            return resposta.content

    def criar(self, tipo, dados):
        conteudo = self.chamar(f"criar {tipo}", f"Criar{NOMES[tipo]}", elemento(tipo, dados))
        if conteudo is None:
            return None
        achado = PADRAO_ID.search(conteudo)
        return int(achado.group(1)) if achado else None

    def obter(self, tipo, identificador):
        self.chamar(f"obter {tipo}", f"Obter{NOMES[tipo]}", elemento("id", identificador))

    def atualizar(self, tipo, identificador, dados):
        corpo = elemento("id", identificador) + elemento(tipo, dados)
        self.chamar(f"atualizar {tipo}", f"Atualizar{NOMES[tipo]}", corpo)

    def remover(self, tipo, identificador):
        self.chamar(f"remover {tipo}", f"Remover{NOMES[tipo]}", elemento("id", identificador))

    def relacionados(self, nome, identificador):
        self.chamar(nome, RELACIONADOS[nome], elemento("id", identificador))


class CrudSoap(HttpUser):
    wait_time = constant(0.5)
    tasks = [CicloSoap]