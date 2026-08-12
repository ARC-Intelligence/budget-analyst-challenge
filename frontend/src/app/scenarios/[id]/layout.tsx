"use client";

import { use, useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { fetchScenario, type Scenario } from "@/lib/api";
import { cn } from "@/lib/utils";

function ViewSwitcher({ id }: { id: string }) {
  const pathname = usePathname();
  const chatActive = pathname.endsWith("/chat");

  return (
    <nav className="flex shrink-0 rounded-full bg-muted p-1">
      <Link
        href={`/scenarios/${id}`}
        className={cn(
          "px-4 py-1.5 text-sm font-medium",
          chatActive
            ? "text-muted-foreground hover:text-foreground"
            : "rounded-full bg-background text-foreground shadow-sm"
        )}
      >
        Budget
      </Link>
      <Link
        href={`/scenarios/${id}/chat`}
        className={cn(
          "px-4 py-1.5 text-sm font-medium",
          chatActive
            ? "rounded-full bg-background text-foreground shadow-sm"
            : "text-muted-foreground hover:text-foreground"
        )}
      >
        Chat
      </Link>
    </nav>
  );
}

export default function ScenarioLayout({
  children,
  params,
}: {
  children: React.ReactNode;
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
    <div className="flex h-dvh flex-col">
      <header className="shrink-0 border-b px-6 py-3">
        <div className="mx-auto flex w-full max-w-7xl items-center justify-between gap-4">
          <div className="flex min-w-0 items-center gap-3">
            <Link
              href="/"
              className="shrink-0 text-sm text-muted-foreground hover:text-foreground"
            >
              ← Scenarios
            </Link>
            {error ? (
              <p className="truncate text-sm text-destructive">{error}</p>
            ) : scenario ? (
              <>
                <h1 className="truncate font-semibold">{scenario.name}</h1>
                <p className="hidden min-w-0 truncate text-sm text-muted-foreground sm:block">
                  {scenario.description}
                </p>
              </>
            ) : null}
          </div>
          <ViewSwitcher id={id} />
        </div>
      </header>
      <div className="flex min-h-0 flex-1 flex-col overflow-y-auto">
        {children}
      </div>
    </div>
  );
}
