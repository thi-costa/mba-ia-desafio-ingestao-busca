# Variáveis de configuração
PYTHON := python3
VENV := .venv
# Ajuste para Windows (bin vs Scripts) se necessário, mas mantendo padrão Linux/macOS
BIN := $(VENV)/bin

.PHONY: help install db ingest chat up clean

help: ## Exibe esta mensagem de ajuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Cria o ambiente virtual e instala as dependências
	@if command -v uv > /dev/null; then \
		echo "Instalando com uv..."; \
		uv sync; \
	else \
		echo "Instalando com venv/pip..."; \
		$(PYTHON) -m venv $(VENV); \
		$(BIN)/pip install --upgrade pip; \
		$(BIN)/pip install -r requirements.txt; \
	fi

db: ## Sobe o banco de dados via Docker Compose
	docker compose up -d

ingest: ## Executa a ingestão do PDF
	@if [ ! -d "$(VENV)" ]; then echo "Erro: Ambiente virtual não encontrado. Rode 'make install' primeiro."; exit 1; fi
	$(BIN)/python src/ingest.py

chat: ## Inicia o chat interativo
	@if [ ! -d "$(VENV)" ]; then echo "Erro: Ambiente virtual não encontrado. Rode 'make install' primeiro."; exit 1; fi
	$(BIN)/python src/chat.py

up: db ingest chat ## Atalho para rodar tudo: Sobe o DB, ingere e inicia o chat

clean: ## Remove arquivos temporários e ambiente virtual
	rm -rf $(VENV)
	find . -type d -name "__pycache__" -exec rm -rf {} +
	docker compose down