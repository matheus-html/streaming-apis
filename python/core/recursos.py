import copy
from dataclasses import dataclass
from typing import Any

import psycopg.errors as erros_pg
from psycopg.types.json import Jsonb

from . import banco, config
from .erros import Conflito, Invalido, NaoEncontrado

FORMATO_INSTANTE = 'YYYY-MM-DD"T"HH24:MI:SS"Z"'

PADROES = {"texto": "", "inteiro": 0, "booleano": False, "lista": [], "json": {}}


@dataclass(frozen=True)
class Campo:
    api: str
    coluna: str
    tipo: str
    obrigatorio: bool = False
    padrao: Any = None
    automatico: str = ""

    @property
    def editavel(self):
        return self.tipo not in ("id", "instante")


def normalizar_paginacao(pagina, tamanho):
    pagina = 1 if pagina is None else pagina
    tamanho = config.TAMANHO_PADRAO if tamanho is None else tamanho
    if not isinstance(pagina, int) or isinstance(pagina, bool) or pagina < 1:
        raise Invalido("pagina deve ser um inteiro maior ou igual a 1")
    if not isinstance(tamanho, int) or isinstance(tamanho, bool) or tamanho < 1:
        raise Invalido("tamanho deve ser um inteiro maior ou igual a 1")
    return pagina, min(tamanho, config.TAMANHO_MAXIMO)


def escapar_like(termo):
    return termo.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class Recurso:
    def __init__(self, nome, tabela, campos, colunas_busca=("nome",), extras_select=()):
        self.nome = nome
        self.tabela = tabela
        self.campos = campos
        self.colunas_busca = colunas_busca
        expressoes = [self._expressao(campo) for campo in campos] + list(extras_select)
        self.select = ", ".join(expressoes)
        self.campos_editaveis = [campo for campo in campos if campo.editavel]

    @staticmethod
    def _expressao(campo):
        if campo.tipo == "instante":
            return (
                "to_char(t." + campo.coluna + " AT TIME ZONE 'UTC', '" + FORMATO_INSTANTE
                + "') AS \"" + campo.api + "\""
            )
        return "t." + campo.coluna + " AS \"" + campo.api + "\""

    @staticmethod
    def _validar(campo, valor):
        tipo = campo.tipo
        if tipo == "texto":
            valido = isinstance(valor, str)
        elif tipo == "inteiro":
            valido = isinstance(valor, int) and not isinstance(valor, bool)
        elif tipo == "booleano":
            valido = isinstance(valor, bool)
        elif tipo == "lista":
            valido = isinstance(valor, list) and all(isinstance(item, str) for item in valor)
        else:
            valido = isinstance(valor, (dict, list))
        if not valido:
            raise Invalido(f"campo '{campo.api}' com tipo inválido")
        if campo.obrigatorio and tipo == "texto" and not valor.strip():
            raise Invalido(f"campo '{campo.api}' é obrigatório")

    @staticmethod
    def _adaptar(campo, valor):
        return Jsonb(valor) if campo.tipo == "json" else valor

    def _valor_criacao(self, campo, dados):
        if campo.api in dados:
            self._validar(campo, dados[campo.api])
            return dados[campo.api]
        if campo.obrigatorio:
            raise Invalido(f"campo '{campo.api}' é obrigatório")
        padrao = campo.padrao if campo.padrao is not None else PADROES[campo.tipo]
        return copy.deepcopy(padrao)

    def validar_extras(self, dados, criando):
        return {}

    def gravar_extras(self, c, identificador, extras):
        return None

    def _buscar(self, c, identificador):
        return c.execute(
            f"SELECT {self.select} FROM {self.tabela} t WHERE t.id = %s", [identificador]
        ).fetchone()

    def _nao_encontrado(self, identificador):
        return NaoEncontrado(f"{self.nome} {identificador} não encontrado")

    def consultar(self, juncao, filtro, parametros, ordem, pagina, tamanho, pai=None):
        pagina, tamanho = normalizar_paginacao(pagina, tamanho)
        base = f"FROM {self.tabela} t {juncao} {filtro}"
        with banco.conexao() as c:
            if pai is not None:
                tabela_pai, nome_pai, identificador_pai = pai
                achou = c.execute(
                    f"SELECT 1 FROM {tabela_pai} WHERE id = %s", [identificador_pai]
                ).fetchone()
                if achou is None:
                    raise NaoEncontrado(f"{nome_pai} {identificador_pai} não encontrado")
            total = c.execute(f"SELECT count(*) AS total {base}", parametros).fetchone()["total"]
            itens = c.execute(
                f"SELECT {self.select} {base} ORDER BY {ordem} LIMIT %s OFFSET %s",
                [*parametros, tamanho, (pagina - 1) * tamanho],
            ).fetchall()
        return {"itens": itens, "pagina": pagina, "tamanho": tamanho, "total": total}

    def listar(self, pagina=None, tamanho=None, termo=None):
        filtro, parametros = "", []
        if termo:
            padrao = "%" + escapar_like(termo) + "%"
            filtro = "WHERE " + " OR ".join(f"t.{coluna} ILIKE %s" for coluna in self.colunas_busca)
            parametros = [padrao] * len(self.colunas_busca)
        return self.consultar("", filtro, parametros, "t.id", pagina, tamanho)

    def obter(self, identificador):
        with banco.conexao() as c:
            linha = self._buscar(c, identificador)
        if linha is None:
            raise self._nao_encontrado(identificador)
        return linha

    def criar(self, dados):
        if not isinstance(dados, dict):
            raise Invalido("o corpo deve ser um objeto")
        colunas, marcadores, valores = [], [], []
        for campo in self.campos:
            if campo.tipo == "id":
                continue
            if campo.tipo == "instante":
                if campo.automatico:
                    colunas.append(campo.coluna)
                    marcadores.append("now()")
                continue
            valor = self._valor_criacao(campo, dados)
            colunas.append(campo.coluna)
            marcadores.append("%s")
            valores.append(self._adaptar(campo, valor))
        extras = self.validar_extras(dados, criando=True)
        try:
            with banco.conexao() as c:
                with c.transaction():
                    identificador = c.execute(
                        f"INSERT INTO {self.tabela} ({', '.join(colunas)}) "
                        f"VALUES ({', '.join(marcadores)}) RETURNING id",
                        valores,
                    ).fetchone()["id"]
                    self.gravar_extras(c, identificador, extras)
                    return self._buscar(c, identificador)
        except erros_pg.ForeignKeyViolation:
            raise Invalido("referência inexistente") from None
        except erros_pg.CheckViolation:
            raise Invalido("valor fora do intervalo permitido") from None

    def atualizar(self, identificador, dados):
        if not isinstance(dados, dict):
            raise Invalido("o corpo deve ser um objeto")
        atribuicoes, valores = [], []
        for campo in self.campos_editaveis:
            if campo.api in dados:
                self._validar(campo, dados[campo.api])
                atribuicoes.append(f"{campo.coluna} = %s")
                valores.append(self._adaptar(campo, dados[campo.api]))
        for campo in self.campos:
            if campo.tipo == "instante" and campo.automatico == "ambos":
                atribuicoes.append(f"{campo.coluna} = now()")
        extras = self.validar_extras(dados, criando=False)
        try:
            with banco.conexao() as c:
                with c.transaction():
                    if atribuicoes:
                        achou = c.execute(
                            f"UPDATE {self.tabela} SET {', '.join(atribuicoes)} "
                            f"WHERE id = %s RETURNING id",
                            [*valores, identificador],
                        ).fetchone()
                    else:
                        achou = c.execute(
                            f"SELECT id FROM {self.tabela} WHERE id = %s", [identificador]
                        ).fetchone()
                    if achou is None:
                        raise self._nao_encontrado(identificador)
                    self.gravar_extras(c, identificador, extras)
                    return self._buscar(c, identificador)
        except erros_pg.ForeignKeyViolation:
            raise Invalido("referência inexistente") from None
        except erros_pg.CheckViolation:
            raise Invalido("valor fora do intervalo permitido") from None

    def remover(self, identificador):
        try:
            with banco.conexao() as c:
                removido = c.execute(
                    f"DELETE FROM {self.tabela} WHERE id = %s RETURNING id", [identificador]
                ).fetchone()
        except erros_pg.ForeignKeyViolation:
            raise Conflito(
                f"{self.nome} {identificador} está em uso e não pode ser removido"
            ) from None
        if removido is None:
            raise self._nao_encontrado(identificador)


class RecursoPlaylist(Recurso):
    def validar_extras(self, dados, criando):
        if "musicaIds" not in dados:
            if criando:
                raise Invalido("campo 'musicaIds' é obrigatório")
            return {}
        ids = dados["musicaIds"]
        if (
            not isinstance(ids, list)
            or not ids
            or any(not isinstance(item, int) or isinstance(item, bool) for item in ids)
        ):
            raise Invalido("musicaIds deve ser uma lista não vazia de inteiros")
        if len(set(ids)) != len(ids):
            raise Invalido("musicaIds não pode ter itens repetidos")
        return {"musicaIds": ids}

    def gravar_extras(self, c, identificador, extras):
        ids = extras.get("musicaIds")
        if ids is None:
            return
        c.execute("DELETE FROM playlist_musica WHERE playlist_id = %s", [identificador])
        with c.cursor() as cursor:
            cursor.executemany(
                "INSERT INTO playlist_musica (playlist_id, musica_id, posicao) VALUES (%s, %s, %s)",
                [(identificador, musica_id, posicao) for posicao, musica_id in enumerate(ids, start=1)],
            )