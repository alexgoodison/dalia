"use client";

import { Badge } from "./ui/badge";
import { getHealthHealthGetQueryKey, useHealthHealthGet } from "../lib/api/client";

export function BackendStatusTag() {
  const { data, isFetching, isError } = useHealthHealthGet({
    query: {
      queryKey: getHealthHealthGetQueryKey(),
      refetchInterval: 60_000,
    },
  });

  if (isFetching) {
    return <Badge variant="outline">Backend: checking…</Badge>;
  }

  if (isError) {
    return <Badge variant="destructive">Backend: offline</Badge>;
  }

  const status = data?.data?.status ?? "unknown";

  return <Badge variant="outline">Backend: {status}</Badge>;
}
