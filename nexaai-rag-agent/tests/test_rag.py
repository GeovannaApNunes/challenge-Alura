"""
tests/test_rag.py

Testes funcionais do agente RAG completo (recuperação + Gemini).

Estes testes fazem chamadas REAIS à API do Google Gemini e precisam de:
    1. GOOGLE_API_KEY configurada no .env
    2. A base já ter sido indexada (python ingest.py)

Por dependerem de rede e de uma API key válida, são pulados
automaticamente (skip) caso a variável de ambiente não esteja definida —
por isso não quebram um `pytest` rodado sem credenciais configuradas.

Executar com:
    pytest tests/test_rag.py -v
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config

pytestmark = pytest.mark.skipif(
    not config.GOOGLE_API_KEY,
    reason="GOOGLE_API_KEY não configurada — testes de RAG real foram pulados.",
)


@pytest.fixture(scope="module")
def agent():
    from rag import NexaAIRag

    rag = NexaAIRag()
    if not rag.has_indexed_documents():
        pytest.skip("Base de conhecimento não indexada. Execute `python ingest.py` primeiro.")
    return rag


# Perguntas cuja resposta ESTÁ nos documentos fornecidos.
QUESTIONS_WITH_ANSWER = [
    "Qual é o preço do plano Business?",
    "Quantos GB de armazenamento possui o plano Starter?",
    "Como recuperar minha senha?",
    "Quem pode convidar novos membros para a organização?",
    "Quais informações a NexaAI coleta sobre os usuários?",
]

# Pergunta cuja resposta NÃO está em nenhum documento.
QUESTION_WITHOUT_ANSWER = "Qual é o preço de um carro da empresa?"


@pytest.mark.parametrize("question", QUESTIONS_WITH_ANSWER)
def test_agent_answers_known_questions(agent, question):
    result = agent.ask(question)
    assert result.answer
    assert len(result.sources) > 0


def test_agent_admits_when_answer_is_not_in_documents(agent):
    result = agent.ask(QUESTION_WITHOUT_ANSWER)
    # O agente deve indicar, de alguma forma, que não encontrou a informação.
    negative_markers = ["não encontrei", "não há", "não consta", "não foi encontrada", "não possuo"]
    answer_lower = result.answer.lower()
    assert any(marker in answer_lower for marker in negative_markers)
