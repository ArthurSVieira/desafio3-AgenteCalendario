# 🧠 Agente de Estudos (`agente-estudos`) — Google ADK + ADK Skills

Agente especialista em organização de estudos e aprendizagem eficaz construído com **Google Agent Development Kit (ADK)** em Python, seguindo a especificação [Agent Skills](https://adk.dev/skills/) e utilizando o [EnvironmentToolset](https://adk.dev/integrations/environment-toolset/) para salvar e replanejar agendas de estudo em CSV compatíveis com o **Google Agenda**.

Conta também com um **Front-End customizado em estética Verde e Preto (Terminal Emerald)** integrado ao servidor FastAPI/ADK, com visualização em tempo real das ferramentas acionadas (`load_skill`, `load_skill_resource`, `ReadFile`, `WriteFile`) e painel de preview/download da agenda CSV.

---

## ✨ Principais Funcionalidades

- **ADK Skills com Divulgação Progressiva (L1 → L2 → L3)**:
  - **L1 (Metadados)**: `name` e `description` no frontmatter do [`SKILL.md`](app/skills/plano-de-estudos/SKILL.md).
  - **L2 (Instruções e Regra de Gating)**: corpo do `SKILL.md`, que impede a geração de planos genéricos quando faltam **objetivo**, **prazo**, **disponibilidade semanal** ou **nível atual**.
  - **L3 (Recursos sob demanda)**: carregados via `load_skill_resource` apenas após o gating (`references/workflow.md`, `references/tecnicas.md`, `references/salvar_agenda.md`, `assets/plano_template.md`, `assets/exemplo_plano.md`).
- **Metodologia de Aprendizagem Baseada em Evidências**:
  - **Revisão Espaçada (1–3–7–14)**, **Prática Ativa (≥ 60% do tempo)**, **Intercalação** e **Checkpoints de Autoavaliação**.
- **Persistência Segura de Arquivos (`EnvironmentToolset`)**:
  - Subclasse `FerramentasDeArquivo` em [`app/agent.py`](app/agent.py) que restringe o `EnvironmentToolset` sobre `LocalEnvironment(working_dir=planos/)` exclusivamente às ferramentas `ReadFile` e `WriteFile` (sem acesso a shell/execução de comandos).
- **Injeção Dinâmica de Data (*Instruction Provider*)**:
  - A função `instrucao_agente(ctx: ReadonlyContext)` injeta a data de hoje e o dia da semana em tempo de execução para interpretar expressões relativas como *"começo segunda que vem"*.
- **Front-End Verde e Preto (`/` e `/ui`) + ADK Dev UI (`/dev-ui/`)**:
  - Chat com renderização de tabelas Markdown, atalhos para os 3 cenários do laboratório, rastreamento de chamadas de ferramentas e painel lateral com os eventos do `plano-de-estudos.csv` e botão de download direto.

---

## 📂 Estrutura do Projeto

```text
agente-estudos/
├── app/
│   ├── agent.py                        # Definição do root_agent, SkillToolset e FerramentasDeArquivo
│   ├── fast_api_app.py                 # Servidor FastAPI integrando ADK + rotas do front-end
│   ├── app_utils/                      # Utilitários de sessão, artefatos, telemetria e A2A
│   └── skills/
│       └── plano-de-estudos/           # Skill ADK empacotada junto ao agente
│           ├── SKILL.md                # L1 + L2 (Regra de Gating)
│           ├── references/             # L3: workflow.md, tecnicas.md, salvar_agenda.md
│           └── assets/                 # L3: plano_template.md, exemplo_plano.md
├── frontend/
│   └── index.html                      # Interface web customizada (estética verde e preto)
├── planos/                             # Diretório de saída do plano-de-estudos.csv (ignorado no Git)
├── services.py                         # Hook de rotas customizadas carregado automaticamente pelo adk web
├── tests/                              # Testes unitários e de integração
└── pyproject.toml                      # Dependências gerenciadas com uv
```

---

## 🚀 Como Configurar e Executar

### 1. Pré-requisitos

- Python 3.11+ e gerenciador de pacotes [`uv`](https://docs.astral.sh/uv/)
- Uma chave de API do [Google AI Studio](https://aistudio.google.com/apikey)

### 2. Configurar Variáveis de Ambiente (`.env`)

Na pasta `agente-estudos/`, crie um arquivo `.env` (nunca versionado no Git):

```bash
cd agente-estudos
read -s -p "Cole sua API Key: " KEY && echo
printf "GOOGLE_GENAI_USE_VERTEXAI=FALSE\nGEMINI_API_KEY=%s\nMODEL=gemini-3.8-flash\n" "$KEY" > .env
```

### 3. Instalar Dependências e Iniciar o Servidor

```bash
uv sync
uv run adk web --allow_origins="*"
```

Acesse no navegador (ou via **Web Preview** na porta `8000`):

- **`http://127.0.0.1:8000/`**: Front-End customizado **Verde & Preto** (com preview e download do CSV).
- **`http://127.0.0.1:8000/dev-ui/`**: Interface de inspeção nativa do **ADK Web** (traces, eventos e grafo).

---

## 🧪 Cenários de Teste

1. **Testar Regra de Gating (Pedido Incompleto)**:
   > *"Quero organizar meus estudos de JavaScript."*
   - O agente solicita apenas as informações faltantes sem carregar recursos L3.
2. **Gerar Plano Completo + Arquivo CSV**:
   > *"Quero aprender JavaScript para fazer meu primeiro projeto de portfólio em 5 semanas. Começo segunda que vem. Posso estudar segunda, quarta e sexta, 2h por dia às 19h. Já sei HTML e CSS, mas nunca programei."*
   - O agente carrega os recursos da skill sob demanda, monta módulos, cronograma com revisões espaçadas, checkpoints e grava `planos/plano-de-estudos.csv` com `WriteFile`.
3. **Replanejamento Inteligente**:
   > *"Perdi as sessões de quarta e sexta da primeira semana. Ajusta o plano?"*
   - O agente lê a agenda atual com `ReadFile`, redistribui os tópicos sem empilhar sessões no mesmo dia e sobrescreve `planos/plano-de-estudos.csv` com `WriteFile`.
