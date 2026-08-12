export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type Scenario = {
  id: number;
  name: string;
  description: string;
  created_at: string;
  line_item_count: number;
};

export type LineItem = {
  id: number;
  scenario: number;
  department: string;
  category: string;
  month: string;
  budget_amount: string;
  actual_amount: string | null;
  notes: string;
};

export type Paginated<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};

export type LineItemInput = Omit<LineItem, "id">;

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });
  if (!res.ok) {
    throw new Error(`Request failed (${res.status})`);
  }
  if (res.status === 204) {
    return undefined as T;
  }
  return res.json() as Promise<T>;
}

export function fetchScenarios() {
  return request<Scenario[]>("/api/scenarios/");
}

export function fetchScenario(id: number | string) {
  return request<Scenario>(`/api/scenarios/${id}/`);
}

export function fetchLineItems(scenarioId: number | string, page = 1) {
  return request<Paginated<LineItem>>(
    `/api/line-items/?scenario=${scenarioId}&page=${page}`
  );
}

export function createLineItem(data: LineItemInput) {
  return request<LineItem>("/api/line-items/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function updateLineItem(id: number, data: Partial<LineItemInput>) {
  return request<LineItem>(`/api/line-items/${id}/`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function deleteLineItem(id: number) {
  return request<void>(`/api/line-items/${id}/`, { method: "DELETE" });
}
