import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

RAIZ = Path(__file__).resolve().parent.parent
RESULTADOS = RAIZ / "analysis" / "results"
SAIDA = RAIZ / "analysis" / "graficos"
LIMITE = 5.0
APIS = ["rest", "soap", "graphql", "grpc"]
NOMES_API = {"rest": "REST", "soap": "SOAP", "graphql": "GraphQL", "grpc": "gRPC"}
LINGUAGENS = ["java", "python"]
NOMES_LINGUAGEM = {"java": "Java", "python": "Python"}
CORES = {"rest": "#257de0", "soap": "#f47230", "graphql": "#00b894", "grpc": "#f2a600"}
ESTILO = {
    "java": {"linestyle": "-", "marker": "o"},
    "python": {"linestyle": "--", "marker": "s"},
}
TEXTO = "#191919"
SECUNDARIO = "#666666"
GRADE = "#e6e6e6"
FASES = {
    "consultas": "Fase 1: consultas (somente leitura)",
    "crud": "Fase 2: CRUD e consultas relacionais",
}

plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.edgecolor": SECUNDARIO,
    "axes.labelcolor": TEXTO,
    "axes.titlecolor": TEXTO,
    "xtick.color": SECUNDARIO,
    "ytick.color": SECUNDARIO,
    "text.color": TEXTO,
    "font.size": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.color": GRADE,
    "grid.linewidth": 0.8,
    "axes.axisbelow": True,
    "savefig.dpi": 160,
    "savefig.bbox": "tight",
})


def carregar(fase):
    dados = {}
    for linguagem in LINGUAGENS:
        for api in APIS:
            caminho = RESULTADOS / fase / f"{linguagem}-{api}.json"
            if caminho.exists():
                dados[(linguagem, api)] = json.loads(caminho.read_text(encoding="utf-8"))
    return dados


def media(valores):
    return sum(valores) / len(valores)


def agregar(registro):
    por_nivel = {}
    for medida in registro["niveis"].values():
        por_nivel.setdefault(medida["usuarios"], []).append(medida)
    pontos = []
    for usuarios in sorted(por_nivel):
        medidas = por_nivel[usuarios]
        rps = [m["rps"] for m in medidas]
        falha = [m["taxaFalha"] * 100 for m in medidas]
        pontos.append({
            "usuarios": usuarios,
            "rps": media(rps),
            "rps_min": min(rps),
            "rps_max": max(rps),
            "falha": media(falha),
            "falha_min": min(falha),
            "falha_max": max(falha),
            "falhou": max(falha) > LIMITE,
        })
    return pontos


def limitado_pelo_teste(registro):
    reais = registro.get("real") or []
    return bool(reais) and not reais[-1]["falhou"]


def vazao_maxima(registro):
    return max(ponto["rps"] for ponto in agregar(registro))


def desenhar_serie(eixo, pontos, chave, api, linguagem, rotulo=None):
    x = [p["usuarios"] for p in pontos]
    y = [p[chave] for p in pontos]
    inferior = [max(p[chave] - p[chave + "_min"], 0) for p in pontos]
    superior = [max(p[chave + "_max"] - p[chave], 0) for p in pontos]
    estilo = ESTILO[linguagem]
    eixo.errorbar(
        x, y, yerr=[inferior, superior], color=CORES[api], linestyle=estilo["linestyle"],
        marker=estilo["marker"], markersize=5, linewidth=2, elinewidth=1.2, capsize=3,
        markeredgecolor="white", markeredgewidth=0.8, label=rotulo,
    )
    falhos = [p for p in pontos if p["falhou"]]
    if falhos:
        eixo.plot(
            [p["usuarios"] for p in falhos], [p[chave] for p in falhos], linestyle="none",
            marker="X", markersize=10, color=TEXTO, markeredgecolor="white", markeredgewidth=1,
            zorder=5,
        )


def preparar_eixos(eixo_rps, eixo_falha):
    eixo_rps.set_ylabel("Vazão (req/s)")
    eixo_rps.set_ylim(bottom=0)
    eixo_falha.set_ylabel("Taxa de falha (%)")
    eixo_falha.set_xlabel("Usuários simultâneos")
    eixo_falha.set_ylim(bottom=0)
    eixo_falha.axhline(LIMITE, color=TEXTO, linestyle=(0, (5, 4)), linewidth=1.2)
    eixo_falha.text(
        0.995, LIMITE, " limite de 5%", transform=eixo_falha.get_yaxis_transform(),
        ha="right", va="bottom", fontsize=9, color=TEXTO,
    )
    eixo_falha.set_xlim(left=0)
    eixo_rps.set_xlim(left=0)


def entrada_falha():
    return Line2D(
        [], [], linestyle="none", marker="X", markersize=10, color=TEXTO,
        markeredgecolor="white", label="carga com falha (>5%)",
    )


def curvas(fase, linguagem, dados):
    series = {api: dados[(linguagem, api)] for api in APIS if (linguagem, api) in dados}
    if not series:
        return None
    figura, (eixo_rps, eixo_falha) = plt.subplots(
        2, 1, figsize=(11, 8), sharex=True, gridspec_kw={"height_ratios": [3, 2], "hspace": 0.1}
    )
    for api, registro in series.items():
        pontos = agregar(registro)
        desenhar_serie(eixo_rps, pontos, "rps", api, linguagem, NOMES_API[api])
        desenhar_serie(eixo_falha, pontos, "falha", api, linguagem)
    preparar_eixos(eixo_rps, eixo_falha)
    entradas, rotulos = eixo_rps.get_legend_handles_labels()
    entradas.append(entrada_falha())
    rotulos.append("carga com falha (>5%)")
    figura.legend(entradas, rotulos, loc="upper center", ncol=len(entradas), frameon=False,
                  bbox_to_anchor=(0.5, 0.96))
    figura.suptitle(
        f"{FASES[fase]} · {NOMES_LINGUAGEM[linguagem]}: comparação entre as APIs",
        fontsize=13, y=1.0,
    )
    destino = SAIDA / f"curvas_{fase}_{linguagem}.png"
    figura.savefig(destino)
    plt.close(figura)
    return destino


def linguagens(fase, dados):
    apis = [api for api in APIS if any((l, api) in dados for l in LINGUAGENS)]
    if not apis:
        return None
    figura, eixos = plt.subplots(
        2, len(apis), figsize=(4.2 * len(apis), 7.5), sharey="row", squeeze=False,
        gridspec_kw={"hspace": 0.12, "wspace": 0.08},
    )
    todos = [agregar(dados[chave]) for chave in dados if chave[1] in apis]
    topo_rps = max(p["rps_max"] for pontos in todos for p in pontos) * 1.08
    topo_falha = max(LIMITE * 1.4, max(p["falha_max"] for pontos in todos for p in pontos) * 1.06)
    for coluna, api in enumerate(apis):
        eixo_rps, eixo_falha = eixos[0][coluna], eixos[1][coluna]
        for linguagem in LINGUAGENS:
            if (linguagem, api) in dados:
                pontos = agregar(dados[(linguagem, api)])
                desenhar_serie(eixo_rps, pontos, "rps", api, linguagem)
                desenhar_serie(eixo_falha, pontos, "falha", api, linguagem)
        preparar_eixos(eixo_rps, eixo_falha)
        eixo_rps.set_ylim(0, topo_rps)
        eixo_falha.set_ylim(0, topo_falha)
        eixo_rps.set_title(NOMES_API[api], fontsize=12)
        eixo_rps.tick_params(labelbottom=False)
        if coluna > 0:
            eixo_rps.set_ylabel("")
            eixo_falha.set_ylabel("")
        eixo_falha.tick_params(axis="x", labelrotation=45)
    entradas = [
        Line2D([], [], color=SECUNDARIO, linewidth=2, label=NOMES_LINGUAGEM[l], **ESTILO[l])
        for l in LINGUAGENS
    ]
    entradas.append(entrada_falha())
    figura.legend(entradas, [e.get_label() for e in entradas], loc="upper center", ncol=3,
                  frameon=False, bbox_to_anchor=(0.5, 0.97))
    figura.suptitle(f"{FASES[fase]}: Java contra Python em cada API", fontsize=13, y=1.02)
    destino = SAIDA / f"linguagens_{fase}.png"
    figura.savefig(destino)
    plt.close(figura)
    return destino


def barras(fase, dados, valor, titulo, rotulo_y, nome, marcar_limite):
    apis = [api for api in APIS if any((l, api) in dados for l in LINGUAGENS)]
    if not apis:
        return None
    figura, eixo = plt.subplots(figsize=(9.5, 5.5))
    largura = 0.36
    maximo = 0
    for deslocamento, linguagem in zip((-largura / 2 - 0.01, largura / 2 + 0.01), LINGUAGENS):
        for posicao, api in enumerate(apis):
            if (linguagem, api) not in dados:
                continue
            registro = dados[(linguagem, api)]
            numero = valor(registro)
            maximo = max(maximo, numero)
            solido = linguagem == "java"
            eixo.bar(
                posicao + deslocamento, numero, largura, color=CORES[api],
                hatch=None if solido else "///", edgecolor=CORES[api] if solido else "white",
                linewidth=0 if solido else 1.2,
            )
            if not solido:
                eixo.bar(posicao + deslocamento, numero, largura, fill=False, edgecolor=CORES[api],
                         linewidth=1.5)
            prefixo = "≥" if marcar_limite and limitado_pelo_teste(registro) else ""
            eixo.text(
                posicao + deslocamento, numero, f"{prefixo}{numero:,.0f}".replace(",", "."),
                ha="center", va="bottom", fontsize=9, color=TEXTO,
            )
    eixo.set_xticks(range(len(apis)))
    eixo.set_xticklabels([NOMES_API[a] for a in apis], fontsize=11)
    eixo.set_ylabel(rotulo_y)
    eixo.set_ylim(0, maximo * 1.12 if maximo else 1)
    eixo.grid(axis="x", visible=False)
    legenda = [
        Patch(facecolor=SECUNDARIO, label="Java"),
        Patch(facecolor="white", edgecolor=SECUNDARIO, hatch="///", label="Python"),
    ]
    eixo.legend(handles=legenda, frameon=False, loc="upper right")
    eixo.set_title(f"{FASES[fase]}\n{titulo}", fontsize=12, loc="left")
    if marcar_limite:
        eixo.annotate(
            "≥ : sem falha até o maior nível testado (limite do teste, não do servidor)",
            xy=(0, -0.13), xycoords="axes fraction", fontsize=9, color=SECUNDARIO,
        )
    destino = SAIDA / nome
    figura.savefig(destino)
    plt.close(figura)
    return destino


def resumir(fase, dados):
    linhas = []
    for linguagem in LINGUAGENS:
        for api in APIS:
            if (linguagem, api) not in dados:
                continue
            registro = dados[(linguagem, api)]
            capacidade = registro.get("capacidade", 0)
            nivel = next((n for n in registro.get("real", []) if n["usuarios"] == capacidade), None)
            p95 = media([r["p95Ms"] for r in nivel["repeticoes"]]) if nivel else 0
            falhas = media([r["taxaFalha"] * 100 for r in nivel["repeticoes"]]) if nivel else 0
            linhas.append({
                "versao": f"{linguagem}-{api}",
                "capacidade_usuarios": capacidade,
                "limitado_pelo_teste": "sim" if limitado_pelo_teste(registro) else "nao",
                "vazao_maxima_rps": round(vazao_maxima(registro), 1),
                "p95_na_capacidade_ms": round(p95),
                "falha_na_capacidade_pct": round(falhas, 2),
            })
    return linhas


def salvar_resumo(todas):
    SAIDA.mkdir(parents=True, exist_ok=True)
    colunas = ["fase", "versao", "capacidade_usuarios", "limitado_pelo_teste", "vazao_maxima_rps",
               "p95_na_capacidade_ms", "falha_na_capacidade_pct"]
    with open(SAIDA / "resumo.csv", "w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=colunas)
        escritor.writeheader()
        escritor.writerows(todas)
    linhas = ["| " + " | ".join(colunas) + " |", "|" + "---|" * len(colunas)]
    for item in todas:
        linhas.append("| " + " | ".join(str(item[c]) for c in colunas) + " |")
    (SAIDA / "resumo.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")


def principal():
    SAIDA.mkdir(parents=True, exist_ok=True)
    todas = []
    for fase in FASES:
        dados = carregar(fase)
        if not dados:
            print(f"sem resultados para a fase {fase}")
            continue
        for linguagem in LINGUAGENS:
            print(curvas(fase, linguagem, dados))
        print(linguagens(fase, dados))
        print(barras(
            fase, dados, lambda r: r.get("capacidade", 0),
            "Capacidade máxima (maior carga com no máximo 5% de falhas em todas as repetições)",
            "Usuários simultâneos", f"capacidade_{fase}.png", True,
        ))
        print(barras(
            fase, dados, vazao_maxima,
            "Vazão máxima observada (req/s)", "Requisições por segundo",
            f"vazao_{fase}.png", False,
        ))
        for item in resumir(fase, dados):
            todas.append({"fase": fase, **item})
    salvar_resumo(todas)
    print(SAIDA / "resumo.csv")


if __name__ == "__main__":
    principal()