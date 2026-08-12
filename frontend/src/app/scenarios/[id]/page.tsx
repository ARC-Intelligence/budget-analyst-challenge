"use client";

import { use } from "react";
import { ScenarioTable } from "@/components/ScenarioTable";

export default function ScenarioPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);

  return (
    <div className="mx-auto w-full max-w-7xl px-6 py-6">
      <ScenarioTable scenarioId={id} />
    </div>
  );
}
