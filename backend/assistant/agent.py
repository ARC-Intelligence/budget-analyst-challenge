from agents import Agent, Runner
from django.conf import settings
from openai.types.responses import ResponseTextDeltaEvent

ALLOWED_ROLES = {"user", "assistant"}


def build_agent(scenario) -> Agent:
    return Agent(
        name="Budget Assistant",
        instructions=(
            "You are a budget analysis assistant helping a finance reviewer "
            f'with the scenario "{scenario.name}" ({scenario.description}). '
            "Answer concisely."
        ),
        model=settings.OPENAI_MODEL,
    )


def _conversation_input(message: str, history: list[dict]) -> list[dict]:
    items = []
    for item in history:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role", "")).lower()
        if role not in ALLOWED_ROLES:
            continue
        if "content" not in item:
            continue
        items.append({"role": role, "content": str(item["content"])})
    items.append({"role": "user", "content": message})
    return items


async def stream_chat(scenario, message: str, history: list[dict]):
    agent = build_agent(scenario)
    result = Runner.run_streamed(agent, input=_conversation_input(message, history))
    async for event in result.stream_events():
        if event.type == "raw_response_event" and isinstance(
            event.data, ResponseTextDeltaEvent
        ):
            yield event.data.delta
