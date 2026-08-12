"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { Chat } from "@/components/Chat";
import { Skeleton } from "@/components/ui/skeleton";
import { fetchScenario, type Scenario } from "@/lib/api";

export default function ScenarioChatPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [scenario, setScenario] = useState<Scenario | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchScenario(id)
      .then(setScenario)
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Failed to load scenario");
      });
  }, [id]);

  return (
    <div className="flex h-dvh flex-col overflow-hidden">
      <header className="shrink-0 border-b px-6 py-3">
        <div className="mx-auto flex max-w-3xl items-center gap-3">
          <Link
            href={`/scenarios/${id}`}
            className="shrink-0 text-sm text-muted-foreground hover:text-foreground"
          >
            ← Back
          </Link>
          {error ? (
            <p className="truncate text-sm text-destructive">{error}</p>
          ) : !scenario ? (
            <Skeleton className="h-5 w-48" />
          ) : (
            <>
              <h1 className="shrink-0 truncate text-base font-semibold tracking-tight">
                {scenario.name}
              </h1>
              <p className="min-w-0 truncate text-sm text-muted-foreground">
                {scenario.description}
              </p>
            </>
          )}
        </div>
      </header>
      <div className="mx-auto flex min-h-0 w-full max-w-3xl flex-1 flex-col px-6 py-4">
        <Chat scenarioId={id} />
      </div>
    </div>
  );
}
