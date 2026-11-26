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
