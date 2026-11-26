import argparse
import csv
import json
import socket
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
RESULTADOS = RAIZ / "analysis" / "results"
TMP = RESULTADOS / "tmp"

VERSOES = [
    "java-rest", "java-soap", "java-graphql", "java-grpc",
    "python-rest", "python-soap", "python-graphql", "python-grpc",
]
LOCUSTFILES = {
    ("consultas", "rest"): "rest_consultas.py",
    ("consultas", "soap"): "soap_consultas.py",
    ("consultas", "graphql"): "graphql_consultas.py",
    ("consultas", "grpc"): "grpc_consultas.py",
    ("crud", "rest"): "rest_crud.py",
    ("crud", "soap"): "soap_crud.py",
    ("crud", "graphql"): "graphql_crud.py",
    ("crud", "grpc"): "grpc_crud.py",
}
MODOS = {
    "completo": {"aquecimento": 10, "medicao": 30, "passos_bissecao": 4, "fracoes": (0.2, 0.4, 0.6, 0.8, 1.0)},
    "rapido": {"aquecimento": 5, "medicao": 15, "passos_bissecao": 3, "fracoes": (0.4, 0.6, 0.8, 1.0)},
}
LIMITE_FALHA = 0.05
REPETICOES = 3
USUARIOS_INICIAIS = 50
FATOR_SONDA = 2
PORTA = 8080
PAUSA_ENTRE_NIVEIS = 5
PROCESSOS = 1
AQUECIMENTO_REFINO = 3200


def executar(comando, **opcoes):
    return subprocess.run(
        comando, cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", errors="replace", **opcoes
    )


def compose(*argumentos, verificar=True):
    resultado = executar(["docker", "compose", *argumentos])
    if verificar and resultado.returncode != 0:
        raise RuntimeError(
            f"docker compose {' '.join(argumentos)} falhou:\n{resultado.stdout}\n{resultado.stderr}"
        )
    return resultado


def aguardar_porta(tempo_limite=120):
    fim = time.time() + tempo_limite
    while time.time() < fim:
        try:
            with socket.create_connection(("localhost", PORTA), timeout=2):
                return
        except OSError:
            time.sleep(1)
    raise RuntimeError(f"a API não respondeu na porta {PORTA} em {tempo_limite}s")


def parar_aplicacoes():
    resultado = executar([
        "docker", "ps", "-a",
        "--filter", "label=com.docker.compose.project=streaming-apis",
        "--format", '{{.Label "com.docker.compose.service"}}',
    ])
    for servico in set(resultado.stdout.split()):
        if servico in VERSOES:
            compose("--profile", servico, "rm", "-sf", servico, verificar=False)


def resetar_banco():
    compose("up", "-d", "--wait", "db")
    compose("exec", "-T", "db", "psql", "-U", "streaming", "-d", "postgres",
            "-c", "DROP DATABASE IF EXISTS streaming WITH (FORCE)")
    compose("exec", "-T", "db", "psql", "-U", "streaming", "-d", "postgres",
            "-c", "CREATE DATABASE streaming TEMPLATE streaming_base")


def preparar_versao(versao):
    parar_aplicacoes()
    resetar_banco()
    compose("--profile", versao, "up", "-d", "--build")
    aguardar_porta()
    time.sleep(3)


def ler_estatisticas(caminho):
    with open(caminho, encoding="utf-8", newline="") as arquivo:
        for linha in csv.DictReader(arquivo):
            if linha["Name"] == "Aggregated":
                requisicoes = int(linha["Request Count"])
                falhas = int(linha["Failure Count"])
                return {
                    "requisicoes": requisicoes,
                    "falhas": falhas,
                    "taxaFalha": falhas / requisicoes if requisicoes else 1.0,
                    "rps": float(linha["Requests/s"]),
                    "mediaMs": float(linha["Average Response Time"]),
                    "p95Ms": float(linha["95%"]),
                    "p99Ms": float(linha["99%"]),
                }
    raise RuntimeError(f"linha Aggregated não encontrada em {caminho}")


def rodar_locust(versao, arquivo, usuarios, modo, etiqueta):
    TMP.mkdir(parents=True, exist_ok=True)
    for antigo in TMP.glob(f"{etiqueta}_*"):
        antigo.unlink()
    config = MODOS[modo]
    taxa = max(usuarios // 4, 1)
    duracao = config["aquecimento"] + config["medicao"]
    inicio = time.time()
    resultado = executar([
        "docker", "compose", "--profile", "loadtest", "run", "--rm", "-T",
        "-e", f"WARMUP={config['aquecimento']}",
        "locust", "-f", f"/app/{arquivo}", "--host", f"http://{versao}:{PORTA}",
        "--headless", "-u", str(usuarios), "-r", str(taxa), "-t", f"{duracao}s",
        "--only-summary", "--csv", f"/results/tmp/{etiqueta}",
        *(["--processes", str(PROCESSOS)] if PROCESSOS > 1 else []),
    ])
    caminho = TMP / f"{etiqueta}_stats.csv"
    if not caminho.exists():
        raise RuntimeError(f"o Locust não gerou resultados:\n{resultado.stdout}\n{resultado.stderr}")
    medida = ler_estatisticas(caminho)
    medida["usuarios"] = usuarios
    medida["segundos"] = round(time.time() - inicio, 1)
    for gerado in TMP.glob(f"{etiqueta}_*"):
        gerado.unlink()
    return medida


class Registro:
    def __init__(self, caminho, refazer):
        self.caminho = caminho
        self.dados = {"niveis": {}}
        if caminho.exists() and not refazer:
            self.dados = json.loads(caminho.read_text(encoding="utf-8"))

    def obter(self, chave):
        return self.dados["niveis"].get(chave)

    def guardar(self, chave, medida):
        self.dados["niveis"][chave] = medida
        self.salvar()

    def salvar(self):
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        self.caminho.write_text(
            json.dumps(self.dados, ensure_ascii=False, indent=2), encoding="utf-8"
        )


def sondar(medir, maximo, passos):
    usuarios = USUARIOS_INICIAIS
    ultimo_ok, primeiro_ruim = 0, None
    while usuarios <= maximo:
        if medir(usuarios)["taxaFalha"] <= LIMITE_FALHA:
            ultimo_ok = usuarios
            usuarios *= FATOR_SONDA
        else:
            primeiro_ruim = usuarios
            break
    if primeiro_ruim is not None:
        baixo, alto = ultimo_ok, primeiro_ruim
        for _ in range(passos):
            meio = (baixo + alto) // 2
            if meio <= baixo or meio >= alto:
                break
            if medir(meio)["taxaFalha"] <= LIMITE_FALHA:
                baixo = meio
            else:
                alto = meio
        ultimo_ok, primeiro_ruim = baixo, alto
    return ultimo_ok, primeiro_ruim


def niveis_reais(ultimo_ok, primeiro_ruim, fracoes):
    base = ultimo_ok if ultimo_ok > 0 else max((primeiro_ruim or USUARIOS_INICIAIS) // 2, 1)
    niveis = {max(1, round(base * fracao)) for fracao in fracoes}
    if primeiro_ruim is not None:
        niveis.add(primeiro_ruim)
    return sorted(niveis)


def testar_real(medir, niveis):
    resultados, capacidade = [], 0
    for usuarios in niveis:
        repeticoes = [medir(usuarios, repeticao) for repeticao in range(1, REPETICOES + 1)]
        falhou = any(r["taxaFalha"] > LIMITE_FALHA for r in repeticoes)
        resultados.append({"usuarios": usuarios, "repeticoes": repeticoes, "falhou": falhou})
        if falhou:
            break
        capacidade = usuarios
    return resultados, capacidade


def resumo(medida):
    return (
        f"{medida['requisicoes']} req, {medida['falhas']} falhas ({medida['taxaFalha'] * 100:.2f}%), "
        f"{medida['rps']:.0f} req/s, media {medida['mediaMs']:.0f} ms, p95 {medida['p95Ms']:.0f} ms"
    )


def refinar(registro, medir_real, versao, niveis):
    novos, _ = testar_real(medir_real, sorted(set(niveis)))
    existentes = {nivel["usuarios"]: nivel for nivel in registro.dados["real"]}
    for nivel in novos:
        existentes[nivel["usuarios"]] = nivel
    reais = [existentes[usuarios] for usuarios in sorted(existentes)]
    capacidade = 0
    for nivel in reais:
        if nivel["falhou"]:
            break
        capacidade = nivel["usuarios"]
    anteriores = set(registro.dados.get("refinado", []))
    registro.dados["real"] = reais
    registro.dados["capacidade"] = capacidade
    registro.dados["refinado"] = sorted(anteriores | {nivel["usuarios"] for nivel in novos})
    registro.salvar()
    print(f"[{versao}] capacidade máxima após refinamento: {capacidade} usuários")
    return registro.dados


def processar_versao(versao, fase, modo, maximo, refazer, rodar=rodar_locust, preparar=preparar_versao,
                     niveis_extra=None):
    api = versao.split("-", 1)[1]
    arquivo = LOCUSTFILES[(fase, api)]
    if not (Path(__file__).parent / arquivo).exists():
        print(f"[{versao}] ainda não existe loadtest/{arquivo}, pulando")
        return None
    registro = Registro(RESULTADOS / fase / f"{versao}.json", refazer)
    if niveis_extra is None and registro.dados.get("concluido"):
        print(f"[{versao}] já concluída ({registro.dados['capacidade']} usuários), pulando")
        return registro.dados
    if niveis_extra is not None and not registro.dados.get("concluido"):
        print(f"[{versao}] sem medição anterior para refinar, pulando")
        return None
    if niveis_extra is None:
        registro.dados.update({"versao": versao, "fase": fase, "modo": modo})
    preparado = False

    def medir_nivel(chave, usuarios, etiqueta, rotulo):
        nonlocal preparado
        existente = registro.obter(chave)
        if existente is not None:
            print(f"[{versao}] {rotulo}: {resumo(existente)} (salvo)")
            return existente
        if not preparado:
            preparar(versao)
            preparado = True
        else:
            time.sleep(PAUSA_ENTRE_NIVEIS)
            aguardar_porta()
        medida = rodar(versao, arquivo, usuarios, modo, etiqueta)
        registro.guardar(chave, medida)
        print(f"[{versao}] {rotulo}: {resumo(medida)} em {medida['segundos']}s")
        return medida

    def medir_sonda(usuarios):
        return medir_nivel(f"sonda:{usuarios}", usuarios, f"{versao}-s{usuarios}", f"sonda {usuarios}u")

    def medir_real(usuarios, repeticao):
        return medir_nivel(
            f"real:{usuarios}:{repeticao}", usuarios, f"{versao}-r{usuarios}-{repeticao}",
            f"real {usuarios}u rep {repeticao}",
        )

    if niveis_extra is not None:
        descartar = set(niveis_extra)
        for usuarios in descartar:
            for repeticao in range(1, REPETICOES + 1):
                registro.dados["niveis"].pop(f"real:{usuarios}:{repeticao}", None)
        registro.dados["real"] = [n for n in registro.dados["real"] if n["usuarios"] not in descartar]
        registro.dados["refinado"] = [u for u in registro.dados.get("refinado", []) if u not in descartar]
        preparar(versao)
        preparado = True
        aquecida = rodar(versao, arquivo, AQUECIMENTO_REFINO, modo, f"{versao}-aquecimento")
        print(f"[{versao}] aquecimento {AQUECIMENTO_REFINO}u (descartado): {resumo(aquecida)}")
        return refinar(registro, medir_real, versao, niveis_extra)

    config = MODOS[modo]
    ultimo_ok, primeiro_ruim = sondar(medir_sonda, maximo, config["passos_bissecao"])
    print(f"[{versao}] sonda: maior nível ok {ultimo_ok}, primeiro com falha {primeiro_ruim}")
    niveis = niveis_reais(ultimo_ok, primeiro_ruim, config["fracoes"])
    resultados, capacidade = testar_real(medir_real, niveis)
    registro.dados.update({
        "sonda": {"ultimoOk": ultimo_ok, "primeiroRuim": primeiro_ruim, "limiteAtingido": primeiro_ruim is None},
        "real": resultados,
        "capacidade": capacidade,
        "concluido": True,
    })
    registro.salvar()
    print(f"[{versao}] capacidade máxima: {capacidade} usuários")
    return registro.dados


def main():
    analisador = argparse.ArgumentParser()
    analisador.add_argument("--versoes", nargs="+", required=True, help="nomes das versões ou 'todas'")
    analisador.add_argument("--fase", choices=["consultas", "crud"], default="consultas")
    analisador.add_argument("--modo", choices=list(MODOS), default="completo")
    analisador.add_argument("--maximo", type=int, default=12800)
    analisador.add_argument("--processos", type=int, default=1)
    analisador.add_argument("--niveis", nargs="+", type=int, default=None)
    analisador.add_argument("--refazer", action="store_true")
    argumentos = analisador.parse_args()
    global PROCESSOS
    PROCESSOS = max(argumentos.processos, 1)
    versoes = VERSOES if argumentos.versoes == ["todas"] else argumentos.versoes
    invalidas = [v for v in versoes if v not in VERSOES]
    if invalidas:
        sys.exit(f"versões inválidas: {invalidas}")
    inicio = time.time()
    for versao in versoes:
        processar_versao(
            versao, argumentos.fase, argumentos.modo, argumentos.maximo, argumentos.refazer,
            niveis_extra=argumentos.niveis,
        )
    parar_aplicacoes()
    print(f"concluído em {(time.time() - inicio) / 60:.1f} min")


if __name__ == "__main__":
    main()