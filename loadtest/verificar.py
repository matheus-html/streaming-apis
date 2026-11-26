from manual import (
    CLIENTES,
    RECURSOS,
    RELACIONADOS,
    dados_musica,
    dados_playlist,
    dados_usuario,
    musicas_sorteadas,
)

import argparse
import sys


class Registro:
    def __init__(self):
        self.linhas = []
        self.falhas = 0

    def conferir(self, descricao, condicao, detalhe=""):
        if condicao:
            self.linhas.append(f"  OK     {descricao}")
        else:
            self.falhas += 1
            self.linhas.append(f"  FALHA  {descricao}  {detalhe}".rstrip())
        return condicao


def identificador(dados):
    if isinstance(dados, dict) and "id" in dados:
        try:
            return int(dados["id"])
        except (TypeError, ValueError):
            return None
    return None


def novos_dados(tipo, dono, rotulo):
    if tipo == "usuario":
        dados = dados_usuario()
    elif tipo == "musica":
        dados = dados_musica()
    else:
        dados = dados_playlist(dono, musicas_sorteadas(3))
    dados["nome"] = rotulo
    return dados


def verificar_recurso(cliente, tipo, registro):
    recurso = RECURSOS[tipo]
    chave_relacionada, _, _ = RELACIONADOS[tipo]
    registro.linhas.append(f"{recurso['rotulo']}")

    lista = cliente.listar(tipo, 1, 3, None)
    itens = lista.dados.get("itens", []) if lista.ok and isinstance(lista.dados, dict) else []
    total = lista.dados.get("total") if lista.ok and isinstance(lista.dados, dict) else None
    registro.conferir("listar", lista.ok and len(itens) > 0, lista.resumo)
    registro.conferir("listar traz o total", total is not None and int(total) >= len(itens), f"total={total}")
    if not itens:
        return None

    primeiro = itens[0]
    primeiro_id = identificador(primeiro)
    busca = cliente.listar(tipo, 1, 10, str(primeiro.get("nome")))
    encontrados = busca.dados.get("itens", []) if busca.ok and isinstance(busca.dados, dict) else []
    registro.conferir(
        "buscar por nome",
        busca.ok and any(identificador(item) == primeiro_id for item in encontrados),
        busca.resumo,
    )

    obtido = cliente.obter(tipo, primeiro_id)
    registro.conferir("obter existente", obtido.ok and identificador(obtido.dados) == primeiro_id, obtido.resumo)

    dono = primeiro_id if tipo == "usuario" else None
    if tipo == "playlist":
        usuarios = cliente.listar("usuario", 1, 1, None)
        dono = identificador(usuarios.dados["itens"][0]) if usuarios.ok and usuarios.dados["itens"] else 1

    criado = cliente.criar(tipo, novos_dados(tipo, dono, "Verificacao Criada"))
    novo_id = identificador(criado.dados) if criado.ok else None
    registro.conferir("criar", criado.ok and novo_id is not None, f"{criado.resumo} {criado.dados if not criado.ok else ''}")
    if novo_id is None:
        return primeiro_id

    lido = cliente.obter(tipo, novo_id)
    registro.conferir(
        "obter o recém-criado",
        lido.ok and isinstance(lido.dados, dict) and lido.dados.get("nome") == "Verificacao Criada",
        lido.resumo,
    )

    alterado = cliente.atualizar(tipo, novo_id, novos_dados(tipo, dono, "Verificacao Atualizada"))
    registro.conferir("atualizar", alterado.ok, f"{alterado.resumo} {alterado.dados if not alterado.ok else ''}")

    relido = cliente.obter(tipo, novo_id)
    registro.conferir(
        "atualização persistiu",
        relido.ok and isinstance(relido.dados, dict) and relido.dados.get("nome") == "Verificacao Atualizada",
        relido.resumo,
    )

    removido = cliente.remover(tipo, novo_id)
    registro.conferir("remover", removido.ok, removido.resumo)

    ausente = cliente.obter(tipo, novo_id)
    registro.conferir("obter removido falha como esperado", not ausente.ok, ausente.resumo)

    relacionados = cliente.relacionados(chave_relacionada, primeiro_id, 1, 5)
    registro.conferir(
        "consulta relacionada",
        relacionados.ok and isinstance(relacionados.dados, dict) and "itens" in relacionados.dados,
        relacionados.resumo,
    )
    return primeiro_id


def principal():
    analisador = argparse.ArgumentParser()
    analisador.add_argument("--api", required=True, choices=list(CLIENTES))
    analisador.add_argument("--host", required=True)
    analisador.add_argument("--versao", default="")
    argumentos = analisador.parse_args()
    cliente = CLIENTES[argumentos.api](argumentos.host)
    registro = Registro()
    titulo = argumentos.versao or cliente.nome
    for tipo in ("usuario", "musica", "playlist"):
        try:
            verificar_recurso(cliente, tipo, registro)
        except Exception as erro:
            registro.falhas += 1
            registro.linhas.append(f"  FALHA  exceção em {tipo}: {type(erro).__name__}: {erro}")
    print(f"== {titulo} ({cliente.nome}) ==")
    print("\n".join(registro.linhas))
    print(f"RESULTADO {titulo}: {'OK' if registro.falhas == 0 else str(registro.falhas) + ' falha(s)'}")
    return 0 if registro.falhas == 0 else 1


if __name__ == "__main__":
    sys.exit(principal())