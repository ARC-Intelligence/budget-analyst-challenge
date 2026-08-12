"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { Chat } from "@/components/Chat";
import { ScenarioTable } from "@/components/ScenarioTable";
import { Skeleton } from "@/components/ui/skeleton";
import { fetchScenario, type Scenario } from "@/lib/api";

export default function ScenarioPage({
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
    <div className="mx-auto flex min-h-full w-full max-w-7xl flex-col px-6 py-6">
      <div className="mb-6">
        <Link
          href="/"
          className="text-sm text-muted-foreground hover:text-foreground"
        >
          ← Back
        </Link>
        {error ? (
          <p className="mt-3 text-sm text-destructive">{error}</p>
        ) : !scenario ? (
          <div className="mt-3 space-y-2">
            <Skeleton className="h-7 w-48" />
            <Skeleton className="h-4 w-96 max-w-full" />
          </div>
        ) : (
          <div className="mt-3">
            <h1 className="text-2xl font-semibold tracking-tight">
              {scenario.name}
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              {scenario.description}
            </p>
          </div>
        )}
      </div>
      <div className="grid flex-1 items-start gap-6 lg:grid-cols-3">
        <div className="min-w-0 lg:col-span-2">
          <ScenarioTable scenarioId={id} />
        </div>
        <div className="lg:sticky lg:top-4 lg:h-[calc(100vh-2rem)] lg:self-start">
          <Chat scenarioId={id} />
        </div>
      </div>
    </div>
  );
}
