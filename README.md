# Desafio MBA Engenharia de Software com IA - Full Cycle

Essa é a documentação que descreve como executar este projeto prático, do MBA em Engenharia de Software com IA.

## Preparação do ambiente
1. Crie um ambiente virtual para execução do projeto:
```bash
# Caso use pip
$ python3 -m venv .venv
# Ou caso use uv
$ uv sync
```
2. Ative o ambiente virtual e instale os pacotes
```bash
# Ative o ambiente virtual
$ source .venv/bin/activate

# Instale as libs com pip (se usar pip)
$ pip install -r requirements.txt

# Instale as libs com uv (caso use uv)
$ uv add -r requirements.txt
# ou
$ uv sync
```

## Execução do projeto

1. Subir o banco de dados
```bash
$ docker compose up -d
```

2. Fazer a ingestão do PDF
```bash
$ python3 src/ingest.py
```

3. Rodar o chat
```bash
$ python3 src/chat.py
```

## Exemplos de utilização
<!-- Adicionar após a solução estar desenvolvida. -->