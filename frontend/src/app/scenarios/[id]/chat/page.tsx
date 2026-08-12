"use client";

import { use } from "react";
import { Chat } from "@/components/Chat";

export default function ScenarioChatPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);

  return (
    <div className="mx-auto flex h-full min-h-0 w-full max-w-3xl flex-col px-6 py-4">
      <Chat scenarioId={id} />
    </div>
  );
}
