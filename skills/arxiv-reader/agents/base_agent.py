"""
Agent Factory — creates LangChain agents / chains.
Uses `create_tool_calling_agent` when tools are supplied,
otherwise returns a simple  prompt | llm  chain.
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import create_agent as create_langchain_agent
import config
from typing import Any

# ── LLM singleton cache ──────────────────────────────────────
_llm_cache: dict[str, ChatOpenAI] = {}


def get_llm(
    temperature: float | None = None,
    max_tokens: int | None = None,
    model: str | None = None,
) -> ChatOpenAI:
    """Return a (cached) ChatOpenAI instance."""
    t = temperature if temperature is not None else config.LLM_TEMPERATURE
    m = max_tokens or config.LLM_MAX_TOKENS
    mdl = model or config.LLM_MODEL
    key = f"{mdl}_{t}_{m}"
    if key not in _llm_cache:
        _llm_cache[key] = ChatOpenAI(
            base_url=config.LLM_BASE_URL,
            api_key=config.LLM_API_KEY,
            model=mdl,
            temperature=t,
            max_tokens=m,
        )
    return _llm_cache[key]


def create_agent(
    system_prompt: str,
    tools: list | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    checkpointer: Any | None = None,
):
    """
    Create a LangChain agent.

    - With tools  → AgentExecutor (tool-calling agent)
    - Without tools → simple  prompt | llm  chain  (invoke with {"messages": ...})
    """
    llm = get_llm(temperature=temperature, max_tokens=max_tokens)

    agent_graph = create_langchain_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt,
        checkpointer=checkpointer
    )
    return agent_graph
