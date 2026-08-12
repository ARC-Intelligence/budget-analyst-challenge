import json
import os

from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt

from budgets.models import Scenario

from .agent import stream_chat
from .sse import sse_event

MISSING_API_KEY_MESSAGE = "OPENAI_API_KEY is not set — add it to your .env"


@csrf_exempt
async def chat(request, scenario_id: int):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed."}, status=405)

    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "Invalid JSON."}, status=400)

    if not isinstance(payload, dict):
        return JsonResponse({"error": "Invalid JSON."}, status=400)

    message = payload.get("message")
    if not isinstance(message, str) or not message:
        return JsonResponse({"error": "Missing message."}, status=400)

    history = payload.get("history", [])
    if not isinstance(history, list):
        history = []

    try:
        scenario = await Scenario.objects.aget(pk=scenario_id)
    except Scenario.DoesNotExist:
        return JsonResponse({"error": "Scenario not found."}, status=404)

    async def event_stream():
        if not os.environ.get("OPENAI_API_KEY"):
            yield sse_event("error", {"message": MISSING_API_KEY_MESSAGE})
            yield sse_event("done", {})
            return
        try:
            async for delta in stream_chat(scenario, message, history):
                yield sse_event("text_delta", {"text": delta})
            yield sse_event("done", {})
        except Exception as exc:
            yield sse_event("error", {"message": str(exc)})
            yield sse_event("done", {})

    iterator = event_stream()
    response = StreamingHttpResponse(iterator, content_type="text/event-stream")
    response["Cache-Control"] = "private, no-store"
    response["X-Accel-Buffering"] = "no"
    return response
