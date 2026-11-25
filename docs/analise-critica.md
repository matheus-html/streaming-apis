# Análise crítica

## 1. Metodologia

**Ambiente.** Todas as versões rodam no mesmo Postgres 16, no mesmo Docker Compose e com os mesmos limites de recursos: API com 2 CPUs e 1 GB, banco com 2 CPUs e 2 GB. O banco é recriado a partir de um template com dados determinísticos (5.000 usuários, 20.000 músicas, 15.000 playlists e 598.223 vínculos) antes de cada versão, e um serviço sobe por vez na porta 8080.

**Carga.** O Locust usa laço fechado: cada usuário virtual espera 0,5 s entre requisições. Há 5 s de aquecimento descartados e 15 s de medição por nível. Uma requisição é falha se retornar erro de protocolo ou passar de 5 s (timeout).

**Capacidade máxima.** É o maior número de usuários simultâneos em que as 3 repetições ficaram com no máximo 5% de falhas. Primeiro uma sonda dobra a carga (50, 100, 200, ...) até a primeira falha acima de 5% e refina o intervalo por bisseção (3 passos). Depois cada nível real (40%, 60%, 80% e 100% do último nível bom, mais o primeiro nível ruim) é medido 3 vezes, parando no primeiro nível reprovado.

**Fases.** A fase 1 só tem consultas: busca por texto, por filtros e relações entre as 3 entidades. A fase 2 mistura criação, leitura, atualização e remoção de usuário, música e playlist com consultas relacionais, em um ciclo de 13 passos. Cada usuário virtual remove só os registros que criou, na ordem playlist, música e usuário.

**Modo.** Todas as medições usaram o modo rápido (15 s de medição, não 30 s). Isso reduz a resolução: os níveis testados são espaçados em 10 a 15%, então a capacidade real fica entre o valor reportado e o primeiro nível reprovado.

## 2. Resultados

Capacidade máxima, em usuários simultâneos:

| API | Java consultas | Python consultas | Java CRUD | Python CRUD |
|---|---|---|---|---|
| REST | 6.400 | 1.920 | 10.240 | 2.200 |
| SOAP | 6.400 | 2.240 | 9.600 | 2.200 |
| GraphQL | 5.120 | 650 | 10.240 | 600 |
| gRPC | 8.000 | 2.240 | ≥25.600 | 1.920 |

Vazão máxima observada, em requisições por segundo (aproximada):

| API | Java consultas | Python consultas | Java CRUD | Python CRUD |
|---|---|---|---|---|
| REST | ~1.400 | 782 | ~2.600 | 712 |
| SOAP | ~1.300 | 571 | ~2.500 | 570 |
| GraphQL | ~1.300 | 340 | ~2.500 | 334 |
| gRPC | ~1.300 | 549 | ~3.900 | 736 |

Os gráficos estão em `analysis/graficos/`: `curvas_<fase>_<linguagem>.png` (API contra API), `linguagens_<fase>.png` (Java contra Python), `capacidade_<fase>.png` e `vazao_<fase>.png`. O resumo numérico está em `resumo.csv` e `resumo.md`, e os dados brutos em `analysis/results/`.

## 3. Análise

### 3.1 Java contra Python

O Java suporta de 2,9 a 7,9 vezes mais usuários que o Python nas consultas e de 4,4 a 17 vezes no CRUD (o gRPC chega a pelo menos 13 vezes, mas limitado pelo teste). O Python satura entre 330 e 780 req/s com 2 workers, enquanto o Java chega a 1.300 req/s nas consultas e a 2.500–3.900 req/s no CRUD. A diferença de capacidade é maior que a de vazão porque, depois que o servidor satura, a latência passa a crescer com o número de usuários, e o Python estoura o timeout de 5 s muito antes.

Fatores prováveis, que não isolei com experimentos separados: o Java usa threads reais e um pool de 32 conexões, enquanto cada processo Python tem 16 conexões e o interpretador serializa o código em Python puro; o JIT também ajuda o Java depois do aquecimento.

### 3.2 API contra API em Java

Nas consultas, as quatro APIs convergem para o mesmo teto de ~1.300 req/s. Esse teto não mudou ao multiplicar o gerador de carga, então ele vem do servidor, com maior probabilidade do Postgres (2 CPUs) executando as consultas. Isso é uma hipótese: não medi o uso de CPU do banco durante o teste. Se o gargalo é o banco, o protocolo quase não altera a vazão, e as diferenças de capacidade (5.120 a 8.000) vêm do comportamento sob sobrecarga: quanto cada API mantém a latência abaixo de 5 s com a fila crescendo.

Uma estimativa grosseira confere: usuários ≈ vazão × (timeout + pausa) dá 1.300 × 5,5 ≈ 7.150, perto dos 6.400 a 8.000 medidos.

No CRUD o teto sobe e as diferenças aparecem. REST, SOAP e GraphQL ficam em 2.500–2.600 req/s e entre 9.600 e 10.240 usuários. O gRPC passa de 3.800 req/s, cerca de 50% a mais, o que é coerente com o formato binário (protobuf) e a multiplexação do HTTP/2. Esse resultado do gRPC deve ser lido com a ressalva da seção 4.

O GraphQL em Java foi o mais baixo nas consultas (5.120). Cada consulta passa pelo parse, pela validação e pela execução do schema, e os campos relacionados são resolvidos separadamente.

### 3.3 API contra API em Python

O GraphQL é muito inferior: capacidade de 650 (consultas) e 600 (CRUD) usuários, e vazão de ~340 req/s, contra 570–780 das outras. Mesmo com o mesmo banco, o custo por requisição é maior, porque o parse, a validação e a execução do schema (Strawberry) rodam em Python puro.

REST, SOAP e gRPC ficam na mesma faixa (1.920 a 2.240 usuários). O REST tem a maior vazão nas consultas (782 req/s), mas não a maior capacidade: a capacidade depende de onde a latência cruza 5 s, não só da vazão. O SOAP é montado à mão, sem biblioteca (a Spyne é incompatível com Python 3.12+), e mesmo assim fica no mesmo patamar do REST.

### 3.4 Consultas contra CRUD

No Java a capacidade do CRUD é maior que a das consultas (por exemplo, 10.240 contra 6.400 no REST). As requisições do CRUD são, em média, mais leves: lookups por chave e escritas pequenas, enquanto as consultas fazem buscas e junções. No Python as duas fases são parecidas, porque o gargalo é o processamento da aplicação.

## 4. Limitações e ameaças à validade

1. **Gerador de carga.** A primeira rodada do Java, com o Locust em 1 processo, chegou ao limite do gerador (~1.500 req/s no CRUD) e reportou "sem falhas até 12.800 usuários", o que subestimava o servidor. Foi refeita com 4 processos e 4 CPUs para o Locust (o limite da API e do banco não mudou). O Python foi medido com 1 processo e 2 CPUs, o que basta: ele satura em menos de 800 req/s, e o Locust passa de 3.000.
2. **Saturação do gerador em cargas muito altas.** Acima de ~12.800 usuários o próprio Locust satura. Prova disso: no REST CRUD, a taxa de falha foi de 4,8% em 12.800 usuários e de 1,7% em 25.600, o que é não monotônico. Os números nessa faixa são menos confiáveis.
3. **gRPC no CRUD (≥25.600).** A vazão cai de 3.885 para ~2.800 req/s e a latência média passa de 5 s sem registrar falhas. O cliente mede o tempo incluindo a espera no laço de eventos, mas o prazo (deadline) do gRPC só conta a chamada, então as falhas são subcontadas. É um limite do teste, e não da capacidade do servidor.
4. **Modo rápido.** Cada medida dura 15 s e a bisseção tem 3 passos. A resolução é de cerca de 10 a 15%, e o aquecimento de 5 s é curto para o JIT do Java chegar ao regime estável.
5. **Uma máquina só.** Gerador, API e banco dividem o mesmo notebook. Cada contêiner tem limite de CPU, mas o cache, o barramento e o escalonador do Windows e do WSL2 são compartilhados.
6. **Registros órfãos.** O CRUD remove só o que cria, mas usuários interrompidos no fim do nível deixam registros para trás (no máximo um ciclo por usuário). O banco é recriado a cada versão, o que limita o efeito.
7. **Falha por timeout.** Contar timeout de 5 s como falha é uma escolha: uma requisição lenta mas correta conta como falha. Um critério diferente (por exemplo, 10 s) mudaria os números, mas não a ordem entre as APIs.

## 5. Decisões de implementação que afetam a comparação

- **Mesmo contrato nas quatro APIs.** Os mesmos casos de uso e as mesmas regras (404, 409 se a música está em uma playlist, validação) e um núcleo de regras compartilhado por linguagem.
- **SOAP manual nas duas linguagens.** Java com DOM e StAX, Python com lxml. O custo de parse e de montagem do XML faz parte do que é medido.
- **GraphQL.** Java com schema primeiro (schema-first) e Python com código primeiro (Strawberry): os dois frameworks têm custos de execução diferentes, e isso entra na comparação.
- **gRPC.** Os campos dinâmicos usam `Struct`, e os números viram `double`. No Java, a conversão passa por `JsonFormat` e por mapas.
- **Pools.** Java com 32 conexões de banco; Python com 2 workers × 16 conexões. O cliente gRPC do Locust compartilha um pool de 32 canais.

## 6. Conclusões

1. Em ambos os estudos, o Java suporta muito mais usuários que o Python com os mesmos recursos: de 3 a 17 vezes.
2. O protocolo pesa menos que a linguagem. Em Java, as APIs ficam na mesma ordem de grandeza (5.120 a 10.240 usuários, exceto o gRPC no CRUD). Em Python, o GraphQL é a exceção negativa.
3. O gRPC é o mais eficiente onde o gargalo não é o banco (CRUD, ~50% mais vazão), mas esse resultado ficou limitado pelo gerador de carga.
4. Nas consultas, o banco parece ser o limitador do Java: as quatro APIs têm o mesmo teto de vazão. Para confirmar, falta medir a CPU do Postgres durante o teste.
5. Os números são válidos como comparação relativa neste ambiente. Os valores absolutos dependem do notebook, do modo rápido e da definição de falha adotada.