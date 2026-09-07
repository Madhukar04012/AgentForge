# AgentForge

A modular Python framework for building tool-using LLM agents.

AgentForge provides a small, composable core:

- **Agents** — pluggable reasoning strategies (ReAct, Planner/Executor).
- **Tools** — typed functions with a central registry and built-ins.
- **Providers** — swappable LLM backends (OpenAI, Anthropic, mock).
- **Memory** — conversation history and a lightweight vector store.
- **Orchestration** — retries, timeouts, and run lifecycle.

## Install

```bash
pip install -e .
```

## Quick start

```python
from agentforge import Agent, ToolRegistry, OpenAIProvider, CalculatorTool

registry = ToolRegistry()
registry.register(CalculatorTool())

agent = Agent(
    provider=OpenAIProvider(model="gpt-4o-mini"),
    tools=registry,
)

print(agent.run("What is 17 * 23?"))
```

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT