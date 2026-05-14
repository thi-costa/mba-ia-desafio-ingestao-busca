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

## Configure as variáveis de ambiente corretamente
Crie um arquivo .env e o preencha corretamente. É importante que o provider que você use para o embeddings seja o mesma para ingestão e o chat (busca vetorial do RAG). Pois as dimensões do embeddings tem um tamanho de vetorização específico.

Especifique o provider usado para a ingestão de dados para que o chat funcione bem na variável `ACTIVE_PROVIDER`.

Segue exemplo do .env:

```plain
GOOGLE_API_KEY="A..."
GOOGLE_EMBEDDING_MODEL='models/gemini-embedding-2'
GOOGLE_CHAT_MODEL="models/gemini-2.5-flash"
ACTIVE_PROVIDER="gemini" # "gemini" ou "openai"

OPENAI_API_KEY="sk-..."
OPENAI_EMBEDDING_MODEL='text-embedding-3-small'
OPENAI_CHAT_MODEL="gpt-5-nano"

DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/rag"
PG_VECTOR_COLLECTION_NAME="rag"

PDF_PATH="document.pdf"
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

Alguns desses comandos estão documentados no Makefile, para ajudar na execução do projeto.

## Exemplos de utilização
* Ingestão de dados:
![alt](docs/test_google_ingest.png)

* Conversação com modelos do Gemini:
![alt](docs/test_google_chat.png)

* Conversação com modelos do OpenAI:
![alt](docs/test_open_ai_chat.png)

