| fase | versao | capacidade_usuarios | limitado_pelo_teste | vazao_util_maxima_rps | p95_na_capacidade_ms | falha_na_capacidade_pct |
|---|---|---|---|---|---|---|
| consultas | java-rest | 6400 | nao | 1316.5 | 4667 | 0.09 |
| consultas | java-soap | 6400 | nao | 1270.5 | 4800 | 0.25 |
| consultas | java-graphql | 5120 | nao | 1207.3 | 3933 | 0.0 |
| consultas | java-grpc | 8000 | nao | 1266.0 | 7167 | 3.01 |
| consultas | python-rest | 1920 | nao | 782.3 | 4200 | 2.46 |
| consultas | python-soap | 2240 | nao | 570.6 | 3767 | 0.0 |
| consultas | python-graphql | 650 | nao | 339.6 | 4200 | 2.84 |
| consultas | python-grpc | 2240 | nao | 533.1 | 5367 | 0.0 |
| crud | java-rest | 10240 | nao | 2620.8 | 10500 | 1.97 |
| crud | java-soap | 9600 | nao | 2436.0 | 9567 | 3.35 |
| crud | java-graphql | 10240 | nao | 2496.7 | 10000 | 4.02 |
| crud | java-grpc | 25600 | sim | 3812.5 | 6833 | 0.0 |
| crud | python-rest | 2200 | nao | 711.9 | 5067 | 3.97 |
| crud | python-soap | 2200 | nao | 570.0 | 4700 | 1.06 |
| crud | python-graphql | 600 | nao | 334.3 | 2567 | 0.53 |
| crud | python-grpc | 1920 | nao | 625.9 | 4600 | 0.94 |
