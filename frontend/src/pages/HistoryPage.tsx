import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { getHistory, listModels } from "../api/inference";
import { ApiClientError } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { AppShell } from "../components/AppShell";
import { StatusBadge } from "../components/StatusBadge";
import type { HistoryItem, HistoryListResponse, ModelSummary } from "../types";

const PAGE_SIZE = 10;
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

export function HistoryPage() {
  const { authState } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();

  const [models, setModels] = useState<ModelSummary[]>([]);
  const [modelsLoading, setModelsLoading] = useState(true);
  const [modelsError, setModelsError] = useState<string | null>(null);
  const [history, setHistory] = useState<HistoryListResponse | null>(null);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [historyError, setHistoryError] = useState<string | null>(null);

  const currentPage = parsePage(searchParams.get("page"));
  const selectedModelId = searchParams.get("modelId") ?? "";

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

  const loadHistoryData = useCallback(async () => {
    if (!authState) {
      return;
    }

    setHistoryLoading(true);
    setHistoryError(null);

    try {
      const response = await getHistory(authState.accessToken, {
        page: currentPage,
        pageSize: PAGE_SIZE,
        modelId: selectedModelId || undefined,
      });
      setHistory(response);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setHistoryError(err.message);
      } else {
        setHistoryError("Unable to load job history.");
      }
    } finally {
      setHistoryLoading(false);
    }
  }, [authState, currentPage, selectedModelId]);

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

  function updateSearch(next: { page?: number; modelId?: string }) {
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

    setSearchParams(nextParams);
  }

  function handleFilterChange(nextModelId: string) {
    updateSearch({ page: 1, modelId: nextModelId });
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
        {items.map((item) => (
          <article className="rounded-2xl bg-white p-5 shadow sm:p-6" key={item.job_id}>
            <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
              <div className="space-y-3">
                <div className="flex flex-wrap items-center gap-3">
                  <StatusBadge status={item.status} />
                  <span className="text-xs font-medium uppercase tracking-wide text-slate-500">{item.engine_id}</span>
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-slate-900">{item.model_id}</h2>
                  <p className="mt-1 break-all text-sm text-slate-500">Job ID: {item.job_id}</p>
                </div>
              </div>

              <Link
                className="rounded-md border border-slate-300 px-4 py-2 text-center text-sm font-medium text-slate-700 hover:bg-slate-50"
                to={`/inference?jobId=${encodeURIComponent(item.job_id)}`}
              >
                View results
              </Link>
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
        ))}
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
                Filter the paginated history feed by model ID returned from `/models`.
              </p>
            </div>

            <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
              <label className="block text-sm font-medium text-slate-700">
                Model
                <select
                  className="mt-1 w-full min-w-60 rounded-md border border-slate-300 bg-white px-3 py-2"
                  disabled={modelsLoading}
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

              <button
                className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                onClick={() => void loadHistoryData()}
                type="button"
              >
                Refresh
              </button>
            </div>
          </div>

          {modelsError ? <p className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{modelsError}</p> : null}

          <div className="mt-5 grid gap-3 sm:grid-cols-3">
            <div className="rounded-xl bg-slate-50 p-4">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Current page</p>
              <p className="mt-2 text-xl font-semibold text-slate-900">{history?.page ?? currentPage}</p>
            </div>
            <div className="rounded-xl bg-slate-50 p-4">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Page size</p>
              <p className="mt-2 text-xl font-semibold text-slate-900">{history?.page_size ?? PAGE_SIZE}</p>
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
                disabled={currentPage <= 1 || historyLoading}
                onClick={() => updateSearch({ page: currentPage - 1, modelId: selectedModelId })}
                type="button"
              >
                Previous
              </button>
              <button
                className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
                disabled={currentPage >= totalPages || historyLoading}
                onClick={() => updateSearch({ page: currentPage + 1, modelId: selectedModelId })}
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
