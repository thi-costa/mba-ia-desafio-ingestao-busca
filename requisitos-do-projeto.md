# Requisitos do projeto
Este documento visa detalhar o projeto de acordo com o escopo solicitado na disciplina.

Foi feita a seguinte definição dos seguintes requisitos:

## Requisitos Funcionais
Estes requisitos detalham espeficações que o projeto deve atender para resolver o problema para o qual foi projetado.

### Requisitos de Negócio
1. O sistema deve permitir a ingestão de arquivos PDF para armazenamento em banco de dados vetorial.
2. O sistema deve oferecer busca semântica baseada exclusivamente no conteúdo dos PDFs carregados.
3. O sistema deve rejeitar perguntas fora do contexto do PDF, retornando a mensagem padrão: *"Não tenho informações necessárias para responder sua pergunta."*

### Requisitos de Usuário
1. O usuário deve poder interagir com o sistema via linha de comando (CLI).
2. O usuário deve poder fazer perguntas em linguagem natural.
3. O sistema deve responder de forma clara e objetiva, sem inferir informações que não estão no PDF.
4. O usuário deve poder executar a ingestão de novos PDFs por meio de um comando específico (`python src/ingest.py`).
5. O usuário deve poder iniciar o chat interativo (`python src/chat.py`).

### Requisitos Técnicos
1. O sistema deve ser implementado em Python.
2. O framework de orquestração deve ser o LangChain.
3. O banco de dados deve ser PostgreSQL com extensão pgVector, executado via Docker e Docker Compose.
4. O script de ingestão deve:
    * Dividir o PDF em chunks de 1000 caracteres com overlap de 150.
    * Converter cada chunk em embeddings.
    * Armazenar os vetores no banco PostgreSQL.
5. O script de busca deve:
    * Vetorizar a pergunta.
    * Consultar os 10 vetores mais relevantes (k=10).
    * Retornar a resposta usando a LLM escolhida.
6. O prompt deve respeitar as regras de resposta:
    * Basear-se apenas no CONTEXTO.
    * Nunca inventar ou usar conhecimento externo.
    * Nunca produzir opiniões ou interpretações.
7. Modelos de embeddings suportados:
    * OpenAI: text-embedding-3-small.
    * Gemini: models/embedding-001.
8. Modelos de LLM suportados:
    * OpenAI: gpt-5-nano.
    * Gemini: gemini-2.5-flash-lite.

## Requisitos não funcionais
Estes requisitos definem as características, qualidades e restrições que o sistema deve ter.

### Requisitos de Produto
1. A interface de linha de comando deve ser simples e intuitiva.
2. O sistema deve ser portável, podendo rodar em qualquer ambiente que suporte Python 3.

### Requisitos Organizacionais
1. O repositório do projeto deve estar no GitHub de forma pública.
2. O código deve seguir a estrutura de pastas pré-definida no enunciado.
3. O README deve conter instruções claras para:
    * Instalação de dependências.
    * Subida do banco de dados com Docker.
    * Execução da ingestão e do chat.
4. O uso de ambiente virtual (venv) é obrigatório para manter o isolamento das dependências.

### Requisitos Externos
1. É obrigatório possuir chaves de API válidas para OpenAI e Google (Gemini).
2. O sistema depende de conectividade com os serviços externos de embeddings e LLMs.
3. O projeto deve utilizar apenas as bibliotecas e pacotes recomendados (LangChain, PyPDFLoader, PGVector, etc.).
4. O projeto deve ser compatível com sistemas operacionais baseados em Linux e Windows (via Docker).
