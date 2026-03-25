import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { clearHistory, deleteHistoryItem, getHistory, listModels } from "../api/inference";
import { ApiClientError } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { AppShell } from "../components/AppShell";
import { StatusBadge } from "../components/StatusBadge";
import type { HistoryItem, HistoryListResponse, HistorySortBy, ModelSummary, SortOrder } from "../types";

const PAGE_SIZE_OPTIONS = [10, 20, 50] as const;
type PageSizeOption = (typeof PAGE_SIZE_OPTIONS)[number];
const DEFAULT_PAGE_SIZE: PageSizeOption = 10;

const SORT_BY_OPTIONS: readonly HistorySortBy[] = ["time", "id", "name"];
const DEFAULT_SORT_BY: HistorySortBy = "time";
const SORT_ORDER_OPTIONS: readonly SortOrder[] = ["desc", "asc"];
const DEFAULT_SORT_ORDER: SortOrder = "desc";

const dateTimeFormatter = new Intl.DateTimeFormat(undefined, {
  dateStyle: "medium",
  timeStyle: "short",
});

function formatTimestamp(value: string) {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return dateTimeFormatter.format(parsed);
}

function formatConfidence(value: number | undefined) {
  if (typeof value !== "number") {
    return "N/A";
  }

  return `${(value * 100).toFixed(1)}%`;
}

function parsePage(rawPage: string | null) {
  const parsed = Number(rawPage);
  if (!Number.isFinite(parsed) || parsed < 1) {
    return 1;
  }

  return Math.floor(parsed);
}

function parsePageSize(rawPageSize: string | null): PageSizeOption {
  const parsed = Number(rawPageSize);
  return PAGE_SIZE_OPTIONS.includes(parsed as PageSizeOption) ? (parsed as PageSizeOption) : DEFAULT_PAGE_SIZE;
}

function parseSortBy(rawSortBy: string | null): HistorySortBy {
  return SORT_BY_OPTIONS.includes(rawSortBy as HistorySortBy) ? (rawSortBy as HistorySortBy) : DEFAULT_SORT_BY;
}

function parseSortOrder(rawSortOrder: string | null): SortOrder {
  return SORT_ORDER_OPTIONS.includes(rawSortOrder as SortOrder) ? (rawSortOrder as SortOrder) : DEFAULT_SORT_ORDER;
}

function getSortByLabel(sortBy: HistorySortBy) {
  if (sortBy === "id") {
    return "Job ID";
  }

  if (sortBy === "name") {
    return "Image name";
  }

  return "Time";
}

export function HistoryPage() {
  const { authState } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();

  const [models, setModels] = useState<ModelSummary[]>([]);
  const [modelsLoading, setModelsLoading] = useState(true);
  const [modelsError, setModelsError] = useState<string | null>(null);
  const [history, setHistory] = useState<HistoryListResponse | null>(null);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [deletingJobId, setDeletingJobId] = useState<string | null>(null);
  const [clearingHistory, setClearingHistory] = useState(false);

  const currentPage = parsePage(searchParams.get("page"));
  const currentPageSize = parsePageSize(searchParams.get("pageSize"));
  const selectedModelId = searchParams.get("modelId") ?? "";
  const currentSortBy = parseSortBy(searchParams.get("sortBy"));
  const currentSortOrder = parseSortOrder(searchParams.get("sortOrder"));
  const hasHistoryItems = (history?.total ?? 0) > 0;
  const actionInProgress = clearingHistory || deletingJobId !== null;

  function updateSearch(next: {
    page?: number;
    modelId?: string;
    pageSize?: PageSizeOption;
    sortBy?: HistorySortBy;
    sortOrder?: SortOrder;
  }) {
    const nextParams = new URLSearchParams(searchParams);

    if (next.page && next.page > 1) {
      nextParams.set("page", String(next.page));
    } else {
      nextParams.delete("page");
    }

    if (next.modelId) {
      nextParams.set("modelId", next.modelId);
    } else {
      nextParams.delete("modelId");
    }

    const nextPageSize = next.pageSize ?? currentPageSize;
    if (nextPageSize === DEFAULT_PAGE_SIZE) {
      nextParams.delete("pageSize");
    } else {
      nextParams.set("pageSize", String(nextPageSize));
    }

    const nextSortBy = next.sortBy ?? currentSortBy;
    if (nextSortBy === DEFAULT_SORT_BY) {
      nextParams.delete("sortBy");
    } else {
      nextParams.set("sortBy", nextSortBy);
    }

    const nextSortOrder = next.sortOrder ?? currentSortOrder;
    if (nextSortOrder === DEFAULT_SORT_ORDER) {
      nextParams.delete("sortOrder");
    } else {
      nextParams.set("sortOrder", nextSortOrder);
    }

    setSearchParams(nextParams);
  }

  const loadModels = useCallback(async () => {
    if (!authState) {
      return;
    }

    setModelsLoading(true);
    setModelsError(null);

    try {
      const response = await listModels(authState.accessToken);
      setModels(response.items);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setModelsError(err.message);
      } else {
        setModelsError("Unable to load model filters.");
      }
    } finally {
      setModelsLoading(false);
    }
  }, [authState]);

  const loadHistoryData = useCallback(async (): Promise<HistoryListResponse | null> => {
    if (!authState) {
      return null;
    }

    setHistoryLoading(true);
    setHistoryError(null);

    try {
      const response = await getHistory(authState.accessToken, {
        page: currentPage,
        pageSize: currentPageSize,
        modelId: selectedModelId || undefined,
        sortBy: currentSortBy,
        sortOrder: currentSortOrder,
      });
      setHistory(response);
      return response;
    } catch (err) {
      if (err instanceof ApiClientError) {
        setHistoryError(err.message);
      } else {
        setHistoryError("Unable to load job history.");
      }
      return null;
    } finally {
      setHistoryLoading(false);
    }
  }, [authState, currentPage, currentPageSize, selectedModelId, currentSortBy, currentSortOrder]);

  useEffect(() => {
    void loadModels();
  }, [loadModels]);

  useEffect(() => {
    void loadHistoryData();
  }, [loadHistoryData]);

  const totalPages = useMemo(() => {
    if (!history) {
      return 1;
    }

    return Math.max(1, Math.ceil(history.total / history.page_size));
  }, [history]);

  const modelNameById = useMemo(() => {
    const lookup = new Map<string, string>();
    for (const model of models) {
      lookup.set(model.model_id, model.display_name);
    }

    return lookup;
  }, [models]);

  const refreshAfterMutation = useCallback(async () => {
    const response = await loadHistoryData();
    if (!response) {
      return;
    }

    if (response.items.length === 0 && response.total > 0 && currentPage > 1) {
      const fallbackPage = Math.max(1, Math.ceil(response.total / currentPageSize));
      if (fallbackPage !== currentPage) {
        updateSearch({
          page: fallbackPage,
          modelId: selectedModelId,
          pageSize: currentPageSize,
          sortBy: currentSortBy,
          sortOrder: currentSortOrder,
        });
      }
    }
  }, [currentPage, currentPageSize, loadHistoryData, selectedModelId, currentSortBy, currentSortOrder]);

  function handleFilterChange(nextModelId: string) {
    updateSearch({
      page: 1,
      modelId: nextModelId,
      pageSize: currentPageSize,
      sortBy: currentSortBy,
      sortOrder: currentSortOrder,
    });
  }

  function handlePageSizeChange(nextPageSize: PageSizeOption) {
    updateSearch({
      page: 1,
      modelId: selectedModelId,
      pageSize: nextPageSize,
      sortBy: currentSortBy,
      sortOrder: currentSortOrder,
    });
  }

  function handleSortByChange(nextSortBy: HistorySortBy) {
    updateSearch({
      page: 1,
      modelId: selectedModelId,
      pageSize: currentPageSize,
      sortBy: nextSortBy,
      sortOrder: currentSortOrder,
    });
  }

  function handleSortOrderChange(nextSortOrder: SortOrder) {
    updateSearch({
      page: 1,
      modelId: selectedModelId,
      pageSize: currentPageSize,
      sortBy: currentSortBy,
      sortOrder: nextSortOrder,
    });
  }

  async function handleDeleteHistoryItem(jobId: string) {
    if (!authState) {
      return;
    }

    const confirmed = window.confirm("Delete this history item? This action cannot be undone.");
    if (!confirmed) {
      return;
    }

    setDeletingJobId(jobId);
    setHistoryError(null);

    try {
      await deleteHistoryItem(authState.accessToken, jobId);
      await refreshAfterMutation();
    } catch (err) {
      if (err instanceof ApiClientError) {
        setHistoryError(err.message);
      } else {
        setHistoryError("Unable to delete history item.");
      }
    } finally {
      setDeletingJobId(null);
    }
  }

  async function handleClearHistory() {
    if (!authState) {
      return;
    }

    const confirmed = window.confirm("Clear all history for your account? This action cannot be undone.");
    if (!confirmed) {
      return;
    }

    setClearingHistory(true);
    setHistoryError(null);

    try {
      await clearHistory(authState.accessToken);
      if (currentPage !== 1) {
        updateSearch({
          page: 1,
          modelId: selectedModelId,
          pageSize: currentPageSize,
          sortBy: currentSortBy,
          sortOrder: currentSortOrder,
        });
      } else {
        await loadHistoryData();
      }
    } catch (err) {
      if (err instanceof ApiClientError) {
        setHistoryError(err.message);
      } else {
        setHistoryError("Unable to clear history.");
      }
    } finally {
      setClearingHistory(false);
    }
  }

  function renderHistoryState(items: HistoryItem[]) {
    if (historyLoading) {
      return <div className="rounded-2xl bg-white p-6 text-sm text-slate-600 shadow">Loading job history...</div>;
    }

    if (historyError) {
      return <div className="rounded-2xl border border-red-200 bg-red-50 p-6 text-sm text-red-700">{historyError}</div>;
    }

    if (items.length === 0) {
      return (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center shadow">
          <h2 className="text-lg font-semibold text-slate-900">No jobs found</h2>
          <p className="mt-2 text-sm text-slate-600">
            Submit an image from the inference page to start building your history.
          </p>
          <Link
            className="mt-4 inline-flex rounded-md bg-brand-500 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
            to="/inference"
          >
            Open inference
          </Link>
        </div>
      );
    }

    return (
      <div className="grid gap-4">
        {items.map((item) => {
          const pictureName =
            typeof item.original_filename === "string" && item.original_filename.trim().length > 0
              ? item.original_filename
              : "Unknown image";
          const selectedModelName = modelNameById.get(item.model_id) ?? item.model_id;

          return (
          <article className="rounded-2xl bg-white p-5 shadow sm:p-6" key={item.job_id}>
            <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
              <div className="space-y-3">
                <div className="flex flex-wrap items-center gap-3">
                  <StatusBadge status={item.status} />
                  <span className="text-xs font-medium uppercase tracking-wide text-slate-500">{item.engine_id}</span>
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-slate-900">{pictureName}</h2>
                  <p className="mt-1 break-all text-sm text-slate-500">Job ID: {item.job_id}</p>
                  <p className="mt-1 text-sm text-slate-600">Model: {selectedModelName}</p>
                </div>
              </div>

              <div className="flex flex-col gap-2 sm:flex-row">
                <Link
                  className="rounded-md border border-slate-300 px-4 py-2 text-center text-sm font-medium text-slate-700 hover:bg-slate-50"
                  to={`/inference?jobId=${encodeURIComponent(item.job_id)}`}
                >
                  View results
                </Link>
                <button
                  className="rounded-md border border-red-300 px-4 py-2 text-sm font-medium text-red-700 hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-60"
                  disabled={actionInProgress || historyLoading}
                  onClick={() => void handleDeleteHistoryItem(item.job_id)}
                  type="button"
                >
                  {deletingJobId === item.job_id ? "Deleting..." : "Delete"}
                </button>
              </div>
            </div>

            <div className="mt-5 grid gap-3 sm:grid-cols-3 xl:grid-cols-4">
              <div className="rounded-xl bg-slate-50 p-4">
                <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Timestamp</p>
                <p className="mt-2 text-sm text-slate-900">{formatTimestamp(item.timestamp)}</p>
              </div>
              <div className="rounded-xl bg-slate-50 p-4">
                <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Defect count</p>
                <p className="mt-2 text-sm text-slate-900">
                  {typeof item.defect_count === "number" ? item.defect_count : "Not available"}
                </p>
              </div>
              <div className="rounded-xl bg-slate-50 p-4">
                <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Max confidence</p>
                <p className="mt-2 text-sm text-slate-900">{formatConfidence(item.max_confidence)}</p>
              </div>
              <div className="rounded-xl bg-slate-50 p-4">
                <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Status</p>
                <p className="mt-2 text-sm text-slate-900 capitalize">{item.status}</p>
              </div>
            </div>
          </article>
          );
        })}
      </div>
    );
  }

  return (
    <AppShell
      title="Inference History"
      description="Browse previously submitted jobs, filter by model, and reopen a specific result in the inference workflow."
    >
      <div className="space-y-6">
        <section className="rounded-2xl bg-white p-5 shadow sm:p-6">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Filters</h2>
              <p className="mt-1 text-sm text-slate-600">
                Filter and sort your history feed using model, page size, and ordering controls.
              </p>
            </div>

            <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
              <label className="block text-sm font-medium text-slate-700">
                Model
                <select
                  className="mt-1 w-full min-w-44 rounded-md border border-slate-300 bg-white px-3 py-2"
                  disabled={modelsLoading || actionInProgress}
                  onChange={(event) => handleFilterChange(event.target.value)}
                  value={selectedModelId}
                >
                  <option value="">All models</option>
                  {models.map((model) => (
                    <option key={model.model_id} value={model.model_id}>
                      {model.display_name}
                    </option>
                  ))}
                </select>
              </label>

              <label className="block text-sm font-medium text-slate-700">
                Sort by
                <select
                  className="mt-1 w-full min-w-32 rounded-md border border-slate-300 bg-white px-3 py-2"
                  disabled={historyLoading || actionInProgress}
                  onChange={(event) => handleSortByChange(event.target.value as HistorySortBy)}
                  value={currentSortBy}
                >
                  <option value="time">Time</option>
                  <option value="id">Job ID</option>
                  <option value="name">Image name</option>
                </select>
              </label>

              <label className="block text-sm font-medium text-slate-700">
                Order
                <select
                  className="mt-1 w-full min-w-28 rounded-md border border-slate-300 bg-white px-3 py-2"
                  disabled={historyLoading || actionInProgress}
                  onChange={(event) => handleSortOrderChange(event.target.value as SortOrder)}
                  value={currentSortOrder}
                >
                  <option value="desc">Desc</option>
                  <option value="asc">Asc</option>
                </select>
              </label>

              <label className="block text-sm font-medium text-slate-700">
                Page size
                <select
                  className="mt-1 w-full min-w-24 rounded-md border border-slate-300 bg-white px-3 py-2"
                  disabled={historyLoading || actionInProgress}
                  onChange={(event) => handlePageSizeChange(Number(event.target.value) as PageSizeOption)}
                  value={currentPageSize}
                >
                  {PAGE_SIZE_OPTIONS.map((sizeOption) => (
                    <option key={sizeOption} value={sizeOption}>
                      {sizeOption}
                    </option>
                  ))}
                </select>
              </label>

              <button
                className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
                disabled={historyLoading || actionInProgress}
                onClick={() => void loadHistoryData()}
                type="button"
              >
                Refresh
              </button>

              <button
                className="rounded-md border border-red-300 px-4 py-2 text-sm font-medium text-red-700 hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-60"
                disabled={!hasHistoryItems || historyLoading || actionInProgress}
                onClick={() => void handleClearHistory()}
                type="button"
              >
                {clearingHistory ? "Clearing..." : "Clear all"}
              </button>
            </div>
          </div>

          {modelsError ? <p className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{modelsError}</p> : null}

          <div className="mt-5 grid gap-3 sm:grid-cols-4">
            <div className="rounded-xl bg-slate-50 p-4">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Current page</p>
              <p className="mt-2 text-xl font-semibold text-slate-900">{history?.page ?? currentPage}</p>
            </div>
            <div className="rounded-xl bg-slate-50 p-4">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Page size</p>
              <p className="mt-2 text-xl font-semibold text-slate-900">{history?.page_size ?? currentPageSize}</p>
            </div>
            <div className="rounded-xl bg-slate-50 p-4">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Sort</p>
              <p className="mt-2 text-sm font-semibold text-slate-900">
                {getSortByLabel(currentSortBy)} / {currentSortOrder.toUpperCase()}
              </p>
            </div>
            <div className="rounded-xl bg-slate-50 p-4">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Total jobs</p>
              <p className="mt-2 text-xl font-semibold text-slate-900">{history?.total ?? 0}</p>
            </div>
          </div>
        </section>

        {renderHistoryState(history?.items ?? [])}

        <section className="rounded-2xl bg-white p-5 shadow sm:p-6">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Pagination</h2>
              <p className="mt-1 text-sm text-slate-600">
                Page {history?.page ?? currentPage} of {totalPages}
              </p>
            </div>

            <div className="flex gap-3">
              <button
                className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
                disabled={currentPage <= 1 || historyLoading || actionInProgress}
                onClick={() =>
                  updateSearch({
                    page: currentPage - 1,
                    modelId: selectedModelId,
                    pageSize: currentPageSize,
                    sortBy: currentSortBy,
                    sortOrder: currentSortOrder,
                  })
                }
                type="button"
              >
                Previous
              </button>
              <button
                className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
                disabled={currentPage >= totalPages || historyLoading || actionInProgress}
                onClick={() =>
                  updateSearch({
                    page: currentPage + 1,
                    modelId: selectedModelId,
                    pageSize: currentPageSize,
                    sortBy: currentSortBy,
                    sortOrder: currentSortOrder,
                  })
                }
                type="button"
              >
                Next
              </button>
            </div>
          </div>
        </section>
      </div>
    </AppShell>
  );
}
