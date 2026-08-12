const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type ChatEvent =
  | { type: "text_delta"; text: string }
  | { type: "done" }
  | { type: "error"; message: string };

export type ChatHistoryItem = {
  role: "user" | "assistant";
  content: string;
};

export async function streamChat(
  scenarioId: number | string,
  message: string,
  history: ChatHistoryItem[],
  onEvent: (e: ChatEvent) => void,
  signal?: AbortSignal
): Promise<void> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}/api/scenarios/${scenarioId}/chat/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "text/event-stream",
      },
      body: JSON.stringify({ message, history }),
      signal,
    });
  } catch (err) {
    if (isAbortError(err)) return;
    onEvent({
      type: "error",
      message: err instanceof Error ? err.message : "Chat request failed",
    });
    return;
  }

  if (!res.ok) {
    onEvent({ type: "error", message: `Request failed (${res.status})` });
    return;
  }

  const reader = res.body?.getReader();
  if (!reader) {
    onEvent({ type: "error", message: "No response body" });
    return;
  }

  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      buffer = flushFrames(buffer, onEvent, false);
    }
    buffer += decoder.decode();
    flushFrames(buffer, onEvent, true);
  } catch (err) {
    if (isAbortError(err)) return;
    onEvent({
      type: "error",
      message: err instanceof Error ? err.message : "Stream failed",
    });
  }
}

function flushFrames(
  buffer: string,
  onEvent: (e: ChatEvent) => void,
  flushTrailing: boolean
): string {
  const normalized = buffer.replace(/\r\n/g, "\n").replace(/\r/g, "\n");
  const parts = normalized.split("\n\n");
  const rest = flushTrailing ? "" : (parts.pop() ?? "");
  for (const frame of parts) {
    dispatchFrame(frame, onEvent);
  }
  if (flushTrailing && rest.trim()) {
    dispatchFrame(rest, onEvent);
  }
  return rest;
}

function dispatchFrame(frame: string, onEvent: (e: ChatEvent) => void) {
  let eventName = "message";
  const dataLines: string[] = [];

  for (const rawLine of frame.split("\n")) {
    const line = rawLine.trimEnd();
    if (!line || line.startsWith(":")) continue;
    const colon = line.indexOf(":");
    const field = colon === -1 ? line : line.slice(0, colon);
    let value = colon === -1 ? "" : line.slice(colon + 1);
    if (value.startsWith(" ")) value = value.slice(1);
    if (field === "event") eventName = value;
    else if (field === "data") dataLines.push(value);
  }

  let data: unknown = {};
  const dataStr = dataLines.join("\n");
  if (dataStr) {
    try {
      data = JSON.parse(dataStr);
    } catch {
      return;
    }
  }

  if (eventName === "text_delta") {
    const text =
      data && typeof data === "object" && "text" in data && typeof data.text === "string"
        ? data.text
        : "";
    onEvent({ type: "text_delta", text });
  } else if (eventName === "done") {
    onEvent({ type: "done" });
  } else if (eventName === "error") {
    const message =
      data &&
      typeof data === "object" &&
      "message" in data &&
      typeof data.message === "string"
        ? data.message
        : "Unknown error";
    onEvent({ type: "error", message });
  }
}

function isAbortError(err: unknown) {
  return (
    (err instanceof DOMException && err.name === "AbortError") ||
    (err instanceof Error && err.name === "AbortError")
  );
}
