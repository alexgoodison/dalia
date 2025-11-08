"use client";

import { useEffect, useMemo, useRef } from "react";
import {
  useInfiniteQuery,
  type InfiniteData,
  type QueryFunctionContext,
} from "@tanstack/react-query";
import type { AxiosError } from "axios";

import { formatAmount } from "../../helpers/currency";
import { formatDate } from "../../helpers/date";
import { trading212TransactionsTrading212TransactionsGet } from "../../lib/api/client";
import type {
  PaginatedHistoryTransactions,
  Trading212TransactionsTrading212TransactionsGetParams,
} from "../../lib/api/model";

type PageParam = { cursor?: string; time?: string } | undefined;

const LIMIT = 50;

const isInfinitePaginatedData = (
  value: unknown
): value is InfiniteData<PaginatedHistoryTransactions, PageParam> => {
  if (
    !value ||
    typeof value !== "object" ||
    !("pages" in value) ||
    !Array.isArray((value as { pages?: unknown }).pages)
  ) {
    return false;
  }

  return true;
};

export default function TransactionsPage() {
  const loadMoreRef = useRef<HTMLDivElement | null>(null);

  const fetchPage = async ({
    pageParam,
  }: QueryFunctionContext<[string], PageParam>): Promise<PaginatedHistoryTransactions> => {
    const params: Trading212TransactionsTrading212TransactionsGetParams = { limit: LIMIT };
    if (pageParam?.cursor) {
      params.cursor = pageParam.cursor;
    }
    if (pageParam?.time) {
      params.time = pageParam.time;
    }
    const response = await trading212TransactionsTrading212TransactionsGet(params);
    return response.data;
  };

  const {
    data,
    isLoading,
    isError,
    error,
    refetch,
    fetchNextPage,
    isFetchingNextPage,
    hasNextPage,
  } = useInfiniteQuery<
    PaginatedHistoryTransactions,
    AxiosError,
    PaginatedHistoryTransactions,
    [string],
    PageParam
  >({
    queryKey: ["/trading212/transactions"],
    initialPageParam: undefined as PageParam,
    queryFn: fetchPage,
    getNextPageParam: (lastPage) =>
      lastPage.nextCursor
        ? { cursor: lastPage.nextCursor, time: lastPage.nextTime ?? undefined }
        : undefined,
    refetchOnWindowFocus: false,
  });

  useEffect(() => {
    const node = loadMoreRef.current;
    if (!node) {
      return;
    }

    const observer = new IntersectionObserver((entries) => {
      if (entries[0]?.isIntersecting && hasNextPage && !isFetchingNextPage) {
        fetchNextPage();
      }
    });

    observer.observe(node);

    return () => {
      observer.disconnect();
    };
  }, [fetchNextPage, hasNextPage, isFetchingNextPage]);

  const transactions = useMemo(
    () => (isInfinitePaginatedData(data) ? data.pages.flatMap((page) => page.items ?? []) : []),
    [data]
  );

  return (
    <div className="min-h-screen bg-linear-to-b from-neutral-50 via-white to-neutral-100 px-6 py-12 font-sans text-neutral-900 dark:from-black dark:via-zinc-900 dark:to-black dark:text-white">
      <main className="mx-auto flex w-full max-w-4xl flex-col gap-8 rounded-3xl bg-white/60 p-8 shadow-sm backdrop-blur dark:bg-zinc-900/60 dark:shadow-none">
        <header className="flex flex-col gap-2">
          <h1 className="text-3xl font-semibold tracking-tight">Trading 212 Transactions</h1>
          <p className="text-sm text-neutral-600 dark:text-neutral-400">
            Streaming your most recent Trading 212 account transactions. Scroll to load more.
          </p>
        </header>

        {isLoading ? (
          <section className="flex items-center justify-center rounded-xl border border-dashed border-neutral-200 p-12 text-sm text-neutral-600 dark:border-neutral-700 dark:text-neutral-300">
            Loading transactions…
          </section>
        ) : isError ? (
          <section className="flex flex-col items-center justify-center gap-4 rounded-xl border border-red-200 bg-red-50/80 p-12 text-center text-sm text-red-700 dark:border-red-400/40 dark:bg-red-950/40 dark:text-red-200">
            <p>We couldn&apos;t load your transactions right now.</p>
            <p className="text-xs text-red-500 dark:text-red-300">
              {error instanceof Error ? error.message : "Unknown error"}
            </p>
            <button
              type="button"
              onClick={() => refetch()}
              className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 dark:focus:ring-offset-zinc-900">
              Try again
            </button>
          </section>
        ) : (
          <section className="flex flex-col gap-4">
            <div className="overflow-x-auto rounded-xl border border-neutral-200 bg-white shadow-sm dark:border-neutral-800 dark:bg-zinc-900 dark:shadow-none">
              <table className="min-w-full divide-y divide-neutral-200 text-left text-sm dark:divide-neutral-800">
                <thead className="bg-neutral-50/70 font-medium uppercase tracking-wide text-neutral-500 dark:bg-zinc-900/60 dark:text-neutral-400">
                  <tr>
                    <th className="px-4 py-3">Date</th>
                    <th className="px-4 py-3">Type</th>
                    <th className="px-4 py-3 text-right">Amount</th>
                    <th className="px-4 py-3">Reference</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-200 dark:divide-neutral-800">
                  {transactions.length === 0 ? (
                    <tr>
                      <td
                        colSpan={4}
                        className="px-4 py-6 text-center text-neutral-500 dark:text-neutral-400">
                        No transactions available yet.
                      </td>
                    </tr>
                  ) : (
                    transactions.map((transaction, index) => (
                      <tr
                        key={`${transaction.reference ?? "tx"}-${index}`}
                        className="bg-white/50 hover:bg-neutral-50 dark:bg-zinc-900/40 dark:hover:bg-zinc-800/60">
                        <td className="px-4 py-3">{formatDate(transaction.dateTime)}</td>
                        <td className="px-4 py-3 capitalize">{transaction.type ?? "—"}</td>
                        <td className="px-4 py-3 text-right font-medium">
                          {formatAmount(transaction.amount)}
                        </td>
                        <td className="px-4 py-3 text-neutral-500 dark:text-neutral-400">
                          {transaction.reference ?? "—"}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            <div ref={loadMoreRef} className="h-12 w-full">
              {isFetchingNextPage && (
                <div className="flex h-full items-center justify-center text-xs text-neutral-500 dark:text-neutral-400">
                  Loading more…
                </div>
              )}
              {!hasNextPage && transactions.length > 0 && (
                <div className="flex h-full items-center justify-center text-xs text-neutral-400 dark:text-neutral-500">
                  You&apos;re all caught up.
                </div>
              )}
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
