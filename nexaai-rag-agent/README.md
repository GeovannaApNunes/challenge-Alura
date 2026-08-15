# NexaAI — Assistente Corporativo

Projeto final do **Challenge Alura Agentes / ONE AI for Tech**: um agente
de inteligência artificial corporativo, com **RAG (Retrieval-Augmented
Generation)** real, capaz de responder perguntas com base em documentos
internos fictícios de uma empresa.

## Sobre o projeto

A **NexaAI** é uma empresa fictícia de tecnologia que oferece uma
plataforma SaaS para gestão de projetos, equipes e operações. Como em
qualquer empresa, seus colaboradores precisam consultar constantemente
documentos internos — base de conhecimento, FAQ de suporte, política de
privacidade, planos e preços, termos de uso — para tirar dúvidas do
dia a dia.

Esse tipo de busca manual é lento e sujeito a erro. Este projeto resolve
o problema construindo um assistente que responde perguntas em
linguagem natural, buscando a informação diretamente nos documentos
oficiais da empresa, em vez de depender de respostas genéricas ou
inventadas.

## Objetivo

Utilizar a técnica de **RAG** para que o agente:

- busque, entre os documentos internos, os trechos mais relevantes para cada pergunta;
- gere uma resposta com base **apenas** nesses trechos;
- indique explicitamente quando a informação não estiver disponível na base de conhecimento, em vez de inventar uma resposta.

## Funcionalidades

- Indexação de documentos PDF internos em um banco vetorial (ChromaDB).
- Busca semântica pelos trechos mais relevantes para cada pergunta.
- Geração de respostas em português via Google Gemini, restrita ao contexto recuperado.
- Indicação das fontes (arquivo + página) utilizadas em cada resposta.
- Interface web simples via Streamlit, com histórico de perguntas da sessão.
- Execução em container Docker, pronta para deploy em uma OCI Compute Instance.

## Arquitetura

```
PDFs (data/)
   │
   ▼
Extração de texto (pypdf)
   │
   ▼
Divisão em chunks (RecursiveCharacterTextSplitter)
   │
   ▼
Geração de embeddings (Google Gemini)
   │
   ▼
Armazenamento vetorial (ChromaDB)
   │
   ▼
Pergunta do usuário (Streamlit)
   │
   ▼
Retriever (busca por similaridade, top-k)
   │
   ▼
Trechos relevantes + pergunta → Prompt com contexto
   │
   ▼
Google Gemini (geração da resposta)
   │
   ▼
Resposta + fontes exibidas na interface (Streamlit)
```

A indexação (`ingest.py`) é uma etapa **separada** da consulta
(`app.py` / `rag.py`): os embeddings dos documentos são gerados uma
única vez e reutilizados em todas as perguntas seguintes.

## Tecnologias

- **Python 3.12**
- **LangChain** (`langchain`, `langchain-chroma`, `langchain-text-splitters`) — orquestração do pipeline de RAG
- **Google Gemini** (`langchain-google-genai`) — geração de embeddings e das respostas
- **ChromaDB** — banco de dados vetorial
- **pypdf** — extração de texto dos PDFs
- **Streamlit** — interface web
- **python-dotenv** — carregamento de variáveis de ambiente
- **Docker / Docker Compose** — empacotamento e execução
- **Oracle Cloud Infrastructure (OCI)** — hospedagem (Compute Instance)

## Documentos utilizados

Todos os documentos são **fictícios**, criados exclusivamente para fins
educacionais do Challenge, e estão em `data/`:

1. `01_base_conhecimento_nexaai.pdf` — visão geral do produto, funcionalidades, permissões e segurança.
2. `02_faq_suporte_nexaai.pdf` — perguntas frequentes sobre uso da plataforma.
3. `03_politica_privacidade_nexaai.pdf` — tratamento de dados dos usuários.
4. `04_planos_e_precos_nexaai.pdf` — planos Starter, Business e Enterprise, preços e regras de cobrança.
5. `05_termos_de_uso_nexaai.pdf` — regras de uso da plataforma.

## Como funciona o RAG

1. **Carregamento**: cada PDF é lido com `pypdf`, extraindo o texto página a página.
2. **Chunking**: o texto de cada página é dividido em pedaços menores (`chunk_size=1000`, `chunk_overlap=150`) com `RecursiveCharacterTextSplitter`, preservando metadados (arquivo de origem e número da página).
3. **Embeddings**: cada chunk é transformado em um vetor numérico pelo modelo de embeddings do Gemini (`text-embedding-004`).
4. **Armazenamento vetorial**: os vetores e metadados são persistidos no ChromaDB (`chroma_db/`), evitando reprocessamento a cada pergunta.
5. **Recuperação**: ao receber uma pergunta, ela também é transformada em embedding e comparada aos vetores armazenados; os `k=4` chunks mais similares são recuperados.
6. **Geração**: os chunks recuperados são inseridos em um prompt estruturado e enviados ao Gemini, que gera a resposta final em português, restrita ao contexto fornecido.

## Estrutura do projeto

```
nexaai-rag-agent/
│
├── app.py                 # Interface Streamlit
├── ingest.py               # Script de indexação (ETL + embeddings)
├── rag.py                  # Lógica de recuperação + geração (RAG)
├── config.py                # Configurações centrais (variáveis de ambiente)
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── Dockerfile
├── docker-compose.yml
│
├── data/                    # PDFs da base de conhecimento
│   ├── 01_base_conhecimento_nexaai.pdf
│   ├── 02_faq_suporte_nexaai.pdf
│   ├── 03_politica_privacidade_nexaai.pdf
│   ├── 04_planos_e_precos_nexaai.pdf
│   └── 05_termos_de_uso_nexaai.pdf
│
├── chroma_db/                # Índice vetorial (gerado localmente, fora do Git)
├── screenshots/               # Evidências visuais da aplicação em execução
├── tests/                      # Testes automatizados
│   ├── test_ingest.py           # Testes offline (PDF/chunking)
│   └── test_rag.py               # Testes do RAG completo (requerem API key)
└── docs/
    └── deploy-oci.md             # Passo a passo do deploy na OCI
```

## Instalação

```bash
git clone https://github.com/SEU_USUARIO/nexaai-rag-agent.git
cd nexaai-rag-agent

python -m venv .venv
```

Ativação do ambiente virtual:

```bash
# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate
```

Instalação das dependências:

```bash
pip install -r requirements.txt
```

Configuração das variáveis de ambiente:

```bash
cp .env.example .env
# edite o arquivo .env e preencha GOOGLE_API_KEY com sua chave do Google AI Studio
```

## Indexação

Antes do primeiro uso (e sempre que os PDFs em `data/` forem alterados),
gere o índice vetorial:

```bash
python ingest.py
```

## Execução

```bash
streamlit run app.py
```

A aplicação abrirá em `http://localhost:8501`.

## Exemplos de perguntas

- "Qual é o preço do plano Business?"
- "Quantos GB de armazenamento o plano Starter possui?"
- "Como recuperar minha senha?"
- "Quem pode adicionar membros à organização?"
- "O que é considerado um incidente crítico?"
- "Qual é o preço de um carro da empresa?" *(fora da base — o agente deve admitir que não sabe)*

## Exemplos de respostas

> **Pergunta:** Qual é o preço do plano Business?
> **Resposta esperada:** O plano Business custa R$ 89,90 por usuário/mês.
> **Fonte:** `04_planos_e_precos_nexaai.pdf`, página 1

> **Pergunta:** Quantos GB de armazenamento o plano Starter possui?
> **Resposta esperada:** O plano Starter inclui 10 GB de armazenamento por organização.
> **Fonte:** `04_planos_e_precos_nexaai.pdf`, página 1

> **Pergunta:** Qual é o preço de um carro da empresa?
> **Resposta esperada:** O agente informa que não encontrou essa informação na base de conhecimento.

*(As respostas exatas dependem da geração do modelo Gemini em tempo de execução; os valores acima refletem o conteúdo real presente nos documentos.)*

## Testes

```bash
pytest tests/ -v
```

- `tests/test_ingest.py` roda **offline** (leitura de PDF e chunking), sem precisar de API key.
- `tests/test_rag.py` executa perguntas reais contra o Gemini e é **pulado automaticamente** se `GOOGLE_API_KEY` não estiver configurada, ou se a base ainda não tiver sido indexada.

## Deploy na OCI

O deploy foi projetado para uma **OCI Compute Instance**, usando Docker.
O passo a passo completo — criação da instância, configuração de rede,
abertura de porta, instalação de dependências, configuração da API key
e execução — está documentado em [`docs/deploy-oci.md`](docs/deploy-oci.md).

Resumo dos comandos na VM (após seguir o guia completo):

```bash
git clone https://github.com/SEU_USUARIO/nexaai-rag-agent.git
cd nexaai-rag-agent
cp .env.example .env   # preencher GOOGLE_API_KEY

docker compose build
docker compose run --rm nexaai python ingest.py
docker compose up -d
```

## Demonstração

> **Status:** deploy na OCI ainda não realizado neste momento. Esta
> seção deve ser preenchida após a execução das etapas de
> `docs/deploy-oci.md`.

- **URL pública:** `[COLOCAR URL AQUI APÓS O DEPLOY]`
- **Screenshot:**

  ![NexaAI em execução](screenshots/agente-oci.png)

  *(Placeholder — a screenshot real deve ser adicionada em `screenshots/agente-oci.png` após a aplicação estar em execução na OCI.)*

## Segurança

- A chave `GOOGLE_API_KEY` é lida exclusivamente de variáveis de ambiente (`.env`), nunca hardcoded no código.
- O arquivo `.env` está listado no `.gitignore` e nunca deve ser commitado.
- O `.env.example` documenta as variáveis necessárias, sem conter valores reais.
- A imagem Docker não copia o `.env` para dentro do container — as variáveis são injetadas em tempo de execução via `env_file` (docker-compose) ou `--env-file`.

## Limitações

- O agente responde exclusivamente com base nos documentos indexados em `data/`; qualquer pergunta fora desse escopo é respondida com uma indicação de que a informação não foi encontrada.
- A qualidade da resposta depende diretamente da qualidade da extração de texto dos PDFs (documentos digitalizados como imagem, sem camada de texto, não seriam processados corretamente por este pipeline).
- O histórico de perguntas é mantido apenas durante a sessão do navegador (em memória), sem persistência entre sessões.

## Melhorias futuras

- Persistir o histórico de conversas por usuário em um banco de dados.
- Adicionar autenticação para uso corporativo real.
- Expandir os testes automatizados com métricas de qualidade de resposta (ex.: avaliação por similaridade semântica).
- Adicionar suporte a outros formatos de documento (DOCX, HTML, páginas de wiki interna).
- Configurar HTTPS e domínio próprio no deploy da OCI.

## Autor

`[SEU NOME AQUI]` — `[LINK DO SEU PERFIL NO GITHUB AQUI]`

Projeto desenvolvido para o **Challenge Alura Agentes / ONE AI for Tech**.
