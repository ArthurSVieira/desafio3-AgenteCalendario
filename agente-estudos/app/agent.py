# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import os
from pathlib import Path

from google.adk.agents import Agent
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.apps import App
from google.adk.environment import LocalEnvironment
from google.adk.models import Gemini
from google.adk.skills import load_skill_from_dir
from google.adk.tools.environment import EnvironmentToolset
from google.adk.tools.skill_toolset import SkillToolset
from google.genai import types

MODEL = os.getenv("MODEL", "gemini-3.8-flash")

BASE_DIR = Path(__file__).resolve().parent
SKILL_DIR = BASE_DIR / "skills" / "plano-de-estudos"
PLANOS_DIR = BASE_DIR.parent / "planos"
PLANOS_DIR.mkdir(parents=True, exist_ok=True)

DIAS_SEMANA = (
    "segunda-feira",
    "terça-feira",
    "quarta-feira",
    "quinta-feira",
    "sexta-feira",
    "sábado",
    "domingo",
)


class FerramentasDeArquivo(EnvironmentToolset):
    """Expõe apenas ReadFile e WriteFile do EnvironmentToolset."""

    async def get_tools(self, readonly_context=None):
        tools = await super().get_tools(readonly_context)
        return [t for t in tools if t.name in ("ReadFile", "WriteFile")]


def instrucao_agente(ctx: ReadonlyContext) -> str:
    """Injeta dinamicamente a data atual na instrução do agente."""
    hoje = datetime.date.today()
    dia_semana = DIAS_SEMANA[hoje.weekday()]
    data_formatada = f"{hoje.strftime('%d/%m/%Y')} ({dia_semana})"

    return (
        f"Hoje é {data_formatada}.\n\n"
        "Você é um mentor especialista em organização de estudos e aprendizagem eficaz. "
        "Responda sempre em português do Brasil.\n"
        "Para criar ou replanejar planos de estudo, utilize a skill `plano-de-estudos` "
        "por meio das ferramentas do SkillToolset, respeitando estritamente a regra de "
        "gating antes de carregar recursos adicionais.\n"
        "Quando salvar ou atualizar a agenda em CSV (`plano-de-estudos.csv`), utilize as "
        "ferramentas de arquivo (`ReadFile` e `WriteFile`)."
    )


plano_de_estudos_skill = load_skill_from_dir(SKILL_DIR)
skill_toolset = SkillToolset(skills=[plano_de_estudos_skill])

file_toolset = FerramentasDeArquivo(
    environment=LocalEnvironment(working_dir=PLANOS_DIR),
)

root_agent = Agent(
    # Keep in sync with create_params.root_agent_name in agents-cli-manifest.yaml:
    # telemetry reports this name as gen_ai.agent.name, and agents-cli reports the
    # manifest's value. Renaming the agent only here makes the two disagree, and
    # anything selecting traces by name stops finding this agent's.
    name="agente_estudos",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    description="Agente que cria e replaneja planos de estudo personalizados com agenda em CSV.",
    instruction=instrucao_agente,
    tools=[skill_toolset, file_toolset],
)

app = App(
    root_agent=root_agent,
    name="app",
)
