# streaming-apis

Comparação de quatro tecnologias de invocação de serviços remotos (SOAP, REST, GraphQL e gRPC), cada uma implementada em Java e em Python, para um mesmo serviço de streaming de música. As 8 versões usam o mesmo Postgres, o mesmo Docker Compose e os mesmos limites de CPU e memória, e foram submetidas a testes de carga com Locust para descobrir a capacidade máxima de cada uma.

Trabalho de Computação Distribuída, UNIFOR. Autor: Matheus Holanda de Sá.

## Resultados

Capacidade máxima: maior número de usuários simultâneos com no máximo 5% de falhas em todas as 3 repetições.

| API | Java consultas | Python consultas | Java CRUD | Python CRUD |
|---|---|---|---|---|
| REST | 6.400 | 1.920 | 10.240 | 2.200 |
| SOAP | 6.400 | 2.240 | 9.600 | 2.200 |
| GraphQL | 5.120 | 650 | 10.240 | 600 |
| gRPC | 8.000 | 2.240 | ≥25.600 | 1.920 |

Vazão útil máxima (requisições com sucesso por segundo):

| API | Java consultas | Python consultas | Java CRUD | Python CRUD |
|---|---|---|---|---|
| REST | 1.316 | 782 | 2.621 | 712 |
| SOAP | 1.270 | 571 | 2.436 | 570 |
| GraphQL | 1.207 | 340 | 2.497 | 334 |
| gRPC | 1.266 | 533 | 3.812 | 626 |

O "≥25.600" do gRPC em Java no CRUD é o maior nível testado, sem falhas: o gerador de carga saturou antes do servidor. A análise completa, com as limitações, está em [`docs/analise-critica.md`](docs/analise-critica.md). Os gráficos estão em [`analysis/graficos/`](analysis/graficos/).

## O serviço

Três recursos: **usuários**, **músicas** e **playlists**. Cada API oferece, para cada recurso, listar (com paginação e busca por nome), obter, criar, atualizar e remover, e mais três consultas relacionais:

- playlists de um usuário;
- músicas de uma playlist;
- playlists que contêm uma música.

Regras iguais em todas as versões: 404 quando não existe, 400 para dados inválidos e 409 ao remover uma música que está em alguma playlist (a chave estrangeira é `ON DELETE RESTRICT`).

Os registros são propositalmente grandes (campos de texto longo, listas e JSON), para que a serialização pese de verdade. O banco é populado de forma determinística (semente 42): 5.000 usuários, 20.000 músicas, 15.000 playlists e 598.223 vínculos entre playlists e músicas.

## Requisitos

- Windows com PowerShell, Docker Desktop (WSL2) com pelo menos 8 CPUs e 8 GB de memória, Git e Python 3.
- Para os gráficos: `pip install matplotlib`.
- Java e Maven não precisam estar instalados: tudo compila dentro do Docker.

Confira o ambiente com `.\scripts\verificar-ambiente.ps1`.

## Estrutura

```
docker-compose.yml     banco, as 8 APIs (perfis), seed e Locust
.env                   limites de CPU e memória (API, banco e Locust)
proto/                 contrato gRPC (streaming.proto)
db/                    schema.sql e seed.py
java/                  core (regras), rest, soap, graphql, grpc (Spring Boot 3.3.5, Java 21)
python/                core (regras), rest, soap, gql, rpc (Python 3.12, FastAPI, Strawberry, grpcio)
loadtest/              scripts do Locust, orquestrador.py, manual.py e verificar.py
scripts/               automação em PowerShell (inclui manual.ps1 e verificar-tudo.ps1)
analysis/              resultados (JSON), graficos.py e gráficos (PNG)
docs/                  analise-critica.md
```

Cada linguagem tem um núcleo (`java/core`, `python/core`) com as regras e o acesso ao banco, compartilhado pelos quatro adaptadores. O que muda entre as versões é só a camada de protocolo.

## Como reproduzir

Todos os comandos rodam na raiz do projeto, no PowerShell.

**1. Banco de dados.** Cria o banco-modelo `streaming_base` (schema e dados) e o banco `streaming`:

```powershell
.\scripts\banco-semear.ps1
```

**2. Subir uma versão** (uma de cada vez, todas na porta 8080):

```powershell
.\scripts\api-subir.ps1 -Perfil java-rest
.\scripts\api-parar.ps1 -Perfil java-rest
```

Perfis: `java-rest`, `java-soap`, `java-graphql`, `java-grpc`, `python-rest`, `python-soap`, `python-graphql`, `python-grpc`.

**3. Teste rápido** (verifica se as 8 versões sobem e respondem, com 10 usuários por 15 s cada):

```powershell
.\scripts\teste-rapido.ps1
```

**4. Testes de capacidade.** Tudo de uma vez (consultas e depois CRUD, depois os gráficos):

```powershell
.\scripts\rodar-tudo.ps1 -Modo rapido
```

Use `-Modo completo` para medições mais longas (30 s por nível em vez de 15 s) e `-Retomar` para continuar de onde parou. Para rodar versões específicas:

```powershell
python -u loadtest\orquestrador.py --versoes java-rest java-grpc --fase consultas --modo rapido --processos 4
```

Parâmetros: `--fase consultas|crud`, `--modo rapido|completo`, `--maximo N` (maior número de usuários da sonda), `--processos N` (processos do Locust; os testes do Java usaram 4), `--niveis ...` (mede níveis específicos para refinar um resultado) e `--refazer`.

**5. Gráficos e resumo:**

```powershell
python analysis\graficos.py
```

Os resultados brutos ficam em `analysis/results/<fase>/<versao>.json` e os gráficos em `analysis/graficos/`.

## Modo manual

Para explorar qualquer versão à mão (sem teste de carga), escolhendo a API e a linguagem:

```powershell
.\scripts\manual.ps1
```

O script lista as 8 versões, sobe a escolhida e abre um menu interativo para listar, buscar por nome, obter, criar, atualizar e remover usuários, músicas e playlists, e para as consultas relacionais. Ele mostra a requisição e a resposta no protocolo escolhido. Ao sair, a versão é parada.

O banco é recriado a partir do modelo (5000 usuários, 20000 músicas, 15000 playlists) a cada execução do `manual.ps1`. Use `-SemReset` para manter os dados da sessão anterior e `-Manter` para deixar a versão no ar depois de sair.

Para conferir de uma só vez que as 8 versões se comportam do mesmo jeito, há um verificador automático:

```powershell
.\scripts\verificar-tudo.ps1
```

Ele sobe cada versão com o banco recém-recriado e executa o mesmo roteiro nos 3 recursos: listar, buscar por nome, obter, criar, atualizar, remover, confirmar que o removido não é mais encontrado e consultar as relações. A saída termina com uma linha `RESULTADO <versao>: OK` por versão; qualquer falha aparece com o motivo. Também aceita um subconjunto: `.\scripts\verificar-tudo.ps1 -Versoes java-rest,python-grpc`.

Também dá para explorar com ferramentas externas, com uma versão no ar:

| API | Como explorar |
|---|---|
| REST | `http://localhost:8080/usuarios`, `/musicas`, `/playlists`, `/saude`. Em Python há também `http://localhost:8080/docs` (Swagger) |
| SOAP | WSDL em `http://localhost:8080/soap` (GET); chamadas por POST no mesmo endereço |
| GraphQL | Java: `http://localhost:8080/graphiql`; Python: `http://localhost:8080/graphql` no navegador |
| gRPC | Porta 8080, sem TLS, com reflexão ativada (por exemplo, `grpcurl -plaintext localhost:8080 list`) |

## Método de teste

- **Carga:** o Locust usa laço fechado. Cada usuário virtual faz uma requisição e espera 0,5 s. Cinco segundos de aquecimento são descartados e há 15 s de medição por nível (modo rápido). Nenhum teste usa dado do cliente: cada usuário virtual escolhe ids e textos de busca aleatórios do banco semeado.
- **Falha:** erro de protocolo ou resposta com mais de 5 s (timeout).
- **Capacidade:** a sonda dobra o número de usuários (50, 100, 200, ...) até a primeira falha acima de 5% e refina por bisseção. Os níveis reais (40%, 60%, 80% e 100% do último nível bom, mais o primeiro ruim) são medidos 3 vezes cada, e a capacidade é o maior nível aprovado nas 3 repetições.
- **Fase 1 (consultas):** só leitura. **Fase 2 (CRUD):** ciclo de 13 passos por usuário virtual (criar, obter, atualizar, consultar relações e remover só o que criou).
- **Justiça:** mesmo banco, mesmos limites (API 2 CPUs e 1 GB, banco 2 CPUs e 2 GB), uma versão por vez, banco recriado a partir do modelo antes de cada versão. O total de conexões com o banco é o mesmo: 32 no Java e 2 processos × 16 no Python.

## Roteiro de defesa

### Onde está cada parte

| O que o professor pode pedir | Onde |
|---|---|
| Contrato REST | `java/rest/src/main/java/streaming/rest/` e `python/rest/app.py` |
| Contrato SOAP (WSDL e operações) | `java/soap/` (`Contrato.java`, `streaming.wsdl`) e `python/soap/contrato.py` |
| Esquema GraphQL | `java/graphql/src/main/resources/graphql/schema.graphqls` e `python/gql/esquema.py` |
| Contrato gRPC | `proto/streaming.proto` |
| Regras de negócio e acesso ao banco | `java/core/` e `python/core/` |
| Banco, esquema e dados | `db/schema.sql`, `db/seed.py` |
| Limites iguais para todas as versões | `docker-compose.yml` e `.env` |
| Scripts de carga (consultas e CRUD) | `loadtest/<api>_consultas.py` e `loadtest/<api>_crud.py` |
| Busca da capacidade máxima | `loadtest/orquestrador.py` |
| Gráficos | `analysis/graficos.py` e `analysis/graficos/` |
| Resultados brutos | `analysis/results/` |
| Análise crítica | `docs/analise-critica.md` |
| Modo manual interativo (cliente de cada protocolo) | `scripts/manual.ps1` e `loadtest/manual.py` |
| Prova de paridade funcional entre as 8 versões | `scripts/verificar-tudo.ps1` e `loadtest/verificar.py` |

### Abertura (cerca de 1 minuto)

"Implementei o mesmo serviço de streaming (usuários, músicas e playlists) em SOAP, REST, GraphQL e gRPC, em Java e em Python: 8 versões que compartilham o banco, o Docker e os mesmos limites de recurso. Para cada versão medi com o Locust a capacidade máxima, que é o maior número de usuários simultâneos com no máximo 5% de falhas em três repetições, em duas fases: só consultas e CRUD. Em resumo: o Java suporta de 3 a 17 vezes mais usuários que o Python; entre as APIs, o gRPC é o mais eficiente onde o banco não é o gargalo, e o GraphQL em Python é o mais lento. Registrei também as limitações: o gRPC em Java no CRUD bateu no limite do gerador de carga."

### Perguntas prováveis

**Como você definiu "capacidade máxima"?**
É o maior número de usuários simultâneos em que as 3 repetições ficaram com no máximo 5% de falhas. Uma sonda dobra a carga até falhar e refina por bisseção; depois cada nível real é medido 3 vezes. Se qualquer repetição passar de 5%, o nível reprova.

**O que conta como falha? Por que 5 s?**
Erro de protocolo (HTTP 5xx, falha do gRPC etc.) ou resposta com mais de 5 s. É uma escolha: uma resposta correta mas muito lenta conta como falha, porque para o usuário ela é inútil. Mudar o limite para 10 s alteraria os números, mas não a ordem entre as APIs.

**Por que um laço fechado com pausa de 0,5 s?**
Cada usuário virtual espera a resposta antes de pedir de novo, como um cliente real. Assim a carga cai sozinha quando o servidor fica lento, e o número de usuários simultâneos é a variável controlada.

**Como você garantiu uma comparação justa?**
Mesmo Postgres, mesmo Compose, mesmos limites de CPU e memória (API 2 CPUs e 1 GB, banco 2 CPUs e 2 GB), uma versão de cada vez e o banco recriado a partir do mesmo modelo antes de cada versão. As conexões com o banco somam 32 nas duas linguagens (32 no Java; 2 processos de 16 no Python). O Python usa 2 processos porque a API tem 2 CPUs.

**Como você sabe que as 8 versões fazem a mesma coisa?**
Escrevi um verificador que roda o mesmo roteiro nas 8 versões: listar, buscar, criar, atualizar, remover e as consultas relacionadas, nos três recursos. Todas passaram, com o banco recriado antes de cada uma.

**Por que o Java ganha tanto do Python?**
Em Java as threads rodam em paralelo de verdade e o JIT compila o código quente. No Python, o código em Python puro (serialização, XML, GraphQL) fica limitado pelo interpretador, e só 2 processos ajudam. Não isolei cada fator em um experimento separado, então trato isso como explicação provável.

**Por que o GraphQL em Python é tão pior (650 usuários)?**
Cada consulta passa por parse, validação e execução do schema em Python puro (Strawberry), e a vazão cai para ~340 req/s, contra 530 a 780 das outras APIs em Python. O banco é o mesmo, então a diferença vem da camada do GraphQL.

**Por que as quatro APIs em Java ficam em ~1.250 req/s nas consultas?**
Como o teto é o mesmo nas quatro e não mudou ao aumentar o gerador de carga, o gargalo parece estar no banco (2 CPUs executando as consultas). É uma hipótese: não medi a CPU do Postgres. O protocolo, nesse caso, quase não importa; muda só como cada API se comporta depois de saturar.

**Por que o gRPC em Java no CRUD aparece como "≥25.600"?**
Porque não falhou até o maior nível testado. A vazão caiu de 3.885 para ~2.800 req/s e a latência passou de 5 s sem falhas registradas: o cliente mede o tempo incluindo a espera no próprio laço de eventos, mas o prazo (deadline) do gRPC só conta a chamada. Ou seja, o gerador de carga saturou antes do servidor. O valor é um limite do teste, e não da capacidade do servidor.

**O Locust não limitou o Java?**
Na primeira rodada sim: com 1 processo ele passava de ~1.500 req/s e não conseguia gerar carga para o Java falhar, o que dava "sem falhas até 12.800". Refiz as 4 versões Java com 4 processos e 4 CPUs para o Locust. Isso não muda o limite da API nem do banco. O Python satura abaixo de 800 req/s e não precisou disso.

**Por que o modo rápido (15 s)?**
Para caber o conjunto completo (8 versões × 2 fases) em um tempo viável no notebook. A consequência é uma resolução de cerca de ±10% na capacidade. Para as três capacidades mais incertas fiz um refinamento com níveis intermediários.

**Os resultados são repetíveis?**
O banco usa semente fixa (42) e é recriado a partir do modelo antes de cada versão. Perto do limite, repetições do mesmo nível divergem (por exemplo, 10,8%, 0% e 4,8% de falhas em REST no CRUD com 11.264 usuários), por isso a capacidade tem resolução de ±10% e diferenças menores entre APIs não são conclusivas.

**Por que implementou o SOAP à mão?**
Em Python a biblioteca habitual (Spyne) não funciona com as versões recentes do Python, e queria o mesmo critério nas duas linguagens. Em Java o XML é tratado com DOM e StAX; em Python, com lxml. O custo de montar e interpretar XML faz parte do que o SOAP custa, então entra na medição.

**Como as APIs diferem em design?**
REST: recursos e verbos HTTP, simples e cacheável. SOAP: contrato formal (WSDL), XML verboso e tipado. GraphQL: o cliente escolhe os campos em uma só rota, o que evita buscar a mais ou a menos, mas custa processamento no servidor. gRPC: contrato em protobuf, formato binário, HTTP/2 com multiplexação e geração de código nas duas pontas.

**O que não ficou perfeito / o que faria com mais tempo?**
Rodar tudo em modo completo, medir a CPU do banco durante o teste (para confirmar o gargalo nas consultas), usar mais de uma máquina (gerador separado do servidor) e medir o gRPC no CRUD com um gerador maior.