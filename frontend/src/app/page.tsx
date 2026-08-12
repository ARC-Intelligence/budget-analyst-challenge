"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { fetchScenarios, type Scenario } from "@/lib/api";

export default function HomePage() {
  const [scenarios, setScenarios] = useState<Scenario[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchScenarios()
      .then(setScenarios)
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Failed to load scenarios");
        setScenarios([]);
      });
  }, []);

  return (
    <div className="mx-auto w-full max-w-3xl px-6 py-10">
      <h1 className="mb-8 text-2xl font-semibold tracking-tight">
        Budget Analyst
      </h1>
      {scenarios === null ? (
        <div className="grid gap-4">
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-24 w-full" />
        </div>
      ) : error ? (
        <p className="text-sm text-destructive">{error}</p>
      ) : scenarios.length === 0 ? (
        <p className="text-sm text-muted-foreground">No scenarios yet.</p>
      ) : (
        <div className="grid gap-4">
          {scenarios.map((scenario) => (
            <Link key={scenario.id} href={`/scenarios/${scenario.id}`}>
              <Card className="transition-colors hover:bg-muted/40">
                <CardHeader>
                  <div className="flex items-start justify-between gap-3">
                    <CardTitle>{scenario.name}</CardTitle>
                    <Badge variant="secondary">
                      {scenario.line_item_count} line items
                    </Badge>
                  </div>
                  <CardDescription>{scenario.description}</CardDescription>
                </CardHeader>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
