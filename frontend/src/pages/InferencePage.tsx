import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { cancelInferenceJob, createInferenceJob, getInferenceJob, getInferenceJobImage, listModels } from "../api/inference";
import { ApiClientError } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { AppShell } from "../components/AppShell";
import { StatusBadge } from "../components/StatusBadge";
import { formatElapsed, parseServerTimestamp } from "../utils/time";
import type { InferenceJobDetail, InferenceJobStatus, InferenceJobSubmission, ModelSummary } from "../types";

const POLL_INTERVAL_MS = 2000;
const SELECTED_MODEL_STORAGE_KEY = "road_defect_selected_model_id";

type EngineFamily = "all" | "rddc2020" | "orddc2024";
type ResolvedEngineFamily = Exclude<EngineFamily, "all"> | "other";

type GroupedModels = {
  key: string;
  label: string;
  items: ModelSummary[];
};

const ENGINE_FAMILY_OPTIONS: Array<{ value: EngineFamily; label: string }> = [
  { value: "all", label: "All" },
  { value: "rddc2020", label: "RDDC2020" },
  { value: "orddc2024", label: "ORDDC2024" },
];

const dateTimeFormatter = new Intl.DateTimeFormat(undefined, {
  dateStyle: "medium",
  timeStyle: "short",
});

function formatTimestamp(value: string | null) {
  if (!value) {
    return "Not available";
  }

  const parsedTimestamp = parseServerTimestamp(value);
  if (parsedTimestamp === null) {
    return value;
  }

  return dateTimeFormatter.format(new Date(parsedTimestamp));
}

function formatDuration(durationMs: number | undefined) {
  if (typeof durationMs !== "number") {
    return "Not available";
  }

  if (durationMs < 1000) {
    return `${durationMs} ms`;
  }

  return `${(durationMs / 1000).toFixed(2)} s`;
}

function formatConfidence(confidence: number | null) {
  if (confidence === null) {
    return "N/A";
  }

  return `${(confidence * 100).toFixed(1)}%`;
}

function getJobStatus(jobDetail: InferenceJobDetail | null, submission: InferenceJobSubmission | null) {
  return jobDetail?.status ?? submission?.status ?? null;
}

function getPersistedModelId(): string {
  try {
    return localStorage.getItem(SELECTED_MODEL_STORAGE_KEY) ?? "";
  } catch {
    return "";
  }
}

function getEngineFamilyFromModel(model: ModelSummary): ResolvedEngineFamily {
  const identity = `${model.model_id} ${model.engine_id}`.toLowerCase();

  if (identity.includes("orddc2024")) {
    return "orddc2024";
  }

  if (identity.includes("rddc2020")) {
    return "rddc2020";
  }

  return "other";
}

function getEngineFamilyLabel(engineFamily: ResolvedEngineFamily) {
  if (engineFamily === "orddc2024") {
    return "ORDDC2024";
  }

  if (engineFamily === "rddc2020") {
    return "RDDC2020";
  }

  return "Other";
}

function getEngineFamilyFilterLabel(engineFamily: EngineFamily) {
  if (engineFamily === "all") {
    return "All";
  }

  return getEngineFamilyLabel(engineFamily);
}

export function InferencePage() {
  const { authState } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();

  const [models, setModels] = useState<ModelSummary[]>([]);
  const [modelsLoading, setModelsLoading] = useState(true);
  const [modelsError, setModelsError] = useState<string | null>(null);
  const [selectedModelId, setSelectedModelId] = useState<string>(() => getPersistedModelId());
  const [selectedEngineFamily, setSelectedEngineFamily] = useState<EngineFamily>("all");
  const [modelSelectionNotice, setModelSelectionNotice] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [submissionError, setSubmissionError] = useState<string | null>(null);
  const [trackedSubmission, setTrackedSubmission] = useState<InferenceJobSubmission | null>(null);
  const [jobDetail, setJobDetail] = useState<InferenceJobDetail | null>(null);
  const [jobError, setJobError] = useState<string | null>(null);
  const [elapsedMs, setElapsedMs] = useState<number | null>(null);
  const [annotatedImageUrl, setAnnotatedImageUrl] = useState<string | null>(null);
  const [annotatedImageLoading, setAnnotatedImageLoading] = useState(false);
  const [annotatedImageError, setAnnotatedImageError] = useState<string | null>(null);
  const [cancellingJob, setCancellingJob] = useState(false);

  const previousStatusRef = useRef<InferenceJobStatus | null>(null);
  const finalSyncJobIdRef = useRef<string | null>(null);
  const pollingInFlightRef = useRef(false);
  const activeJobIdRef = useRef<string | null>(null);
  const annotatedImageUrlRef = useRef<string | null>(null);

  const jobIdFromRoute = searchParams.get("jobId");
  const previewUrl = useMemo(() => {
    if (!selectedFile) {
      return null;
    }

    return URL.createObjectURL(selectedFile);
  }, [selectedFile]);

  const updateAnnotatedImageUrl = useCallback((nextUrl: string | null) => {
    if (annotatedImageUrlRef.current) {
      URL.revokeObjectURL(annotatedImageUrlRef.current);
      annotatedImageUrlRef.current = null;
    }

    annotatedImageUrlRef.current = nextUrl;
    setAnnotatedImageUrl(nextUrl);
  }, []);

  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  useEffect(() => {
    return () => {
      if (annotatedImageUrlRef.current) {
        URL.revokeObjectURL(annotatedImageUrlRef.current);
        annotatedImageUrlRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    try {
      if (selectedModelId) {
        localStorage.setItem(SELECTED_MODEL_STORAGE_KEY, selectedModelId);
      } else {
        localStorage.removeItem(SELECTED_MODEL_STORAGE_KEY);
      }
    } catch {
      // Ignore localStorage access issues.
    }
  }, [selectedModelId]);

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
        setModelsError("Unable to load model options.");
      }
    } finally {
      setModelsLoading(false);
    }
  }, [authState]);

  const loadJob = useCallback(
    async (jobId: string) => {
      if (!authState) {
        return;
      }

      try {
        const response = await getInferenceJob(authState.accessToken, jobId);
        if (activeJobIdRef.current !== jobId) {
          return;
        }

        setJobDetail(response);
        setTrackedSubmission({
          job_id: response.job_id,
          status: response.status,
          model_id: response.model_id,
          engine_id: response.engine_id,
        });
        setJobError(null);
      } catch (err) {
        if (activeJobIdRef.current !== jobId) {
          return;
        }

        if (err instanceof ApiClientError) {
          setJobError(err.message);
        } else {
          setJobError("Unable to load the job status.");
        }
      }
    },
    [authState],
  );

  useEffect(() => {
    void loadModels();
  }, [loadModels]);

  const filteredModels = useMemo(() => {
    if (selectedEngineFamily === "all") {
      return models;
    }

    return models.filter((model) => getEngineFamilyFromModel(model) === selectedEngineFamily);
  }, [models, selectedEngineFamily]);

  const groupedFilteredModels = useMemo<GroupedModels[]>(() => {
    const groups = new Map<string, GroupedModels>();

    for (const model of filteredModels) {
      const existingGroup = groups.get(model.engine_id);
      if (existingGroup) {
        existingGroup.items.push(model);
        continue;
      }

      const engineFamily = getEngineFamilyFromModel(model);
      groups.set(model.engine_id, {
        key: model.engine_id,
        label: `${getEngineFamilyLabel(engineFamily)} (${model.engine_id})`,
        items: [model],
      });
    }

    return Array.from(groups.values());
  }, [filteredModels]);

  useEffect(() => {
    if (models.length === 0) {
      if (!modelsLoading) {
        setSelectedModelId("");
        setModelSelectionNotice(`No models are available under ${getEngineFamilyFilterLabel(selectedEngineFamily)}.`);
      } else {
        setModelSelectionNotice(null);
      }
      return;
    }

    const selectedModelStillVisible = filteredModels.some((model) => model.model_id === selectedModelId);
    if (selectedModelId && selectedModelStillVisible) {
      setModelSelectionNotice(null);
      return;
    }

    const fallbackModel = filteredModels[0] ?? null;
    const nextModelId = fallbackModel?.model_id ?? "";

    if (selectedModelId && fallbackModel) {
      const nextEngineLabel = getEngineFamilyFilterLabel(selectedEngineFamily);
      setModelSelectionNotice(
        `Selected model is unavailable under ${nextEngineLabel}. Switched to ${fallbackModel.display_name}.`,
      );
    } else if (selectedModelId && !fallbackModel) {
      setModelSelectionNotice(
        `Selected model is unavailable under ${getEngineFamilyFilterLabel(selectedEngineFamily)}. No models match this filter.`,
      );
    } else if (!selectedModelId && !fallbackModel && !modelsLoading) {
      setModelSelectionNotice(`No models are available under ${getEngineFamilyFilterLabel(selectedEngineFamily)}.`);
    } else {
      setModelSelectionNotice(null);
    }

    setSelectedModelId(nextModelId);
  }, [filteredModels, models.length, modelsLoading, selectedEngineFamily, selectedModelId]);

  useEffect(() => {
    if (!jobIdFromRoute) {
      activeJobIdRef.current = null;
      pollingInFlightRef.current = false;
      setJobDetail(null);
      setModelSelectionNotice(null);
      setTrackedSubmission(null);
      setJobError(null);
      setCancellingJob(false);
      previousStatusRef.current = null;
      finalSyncJobIdRef.current = null;
      return;
    }

    activeJobIdRef.current = jobIdFromRoute;
    previousStatusRef.current = null;
    finalSyncJobIdRef.current = null;
    void loadJob(jobIdFromRoute);
  }, [jobIdFromRoute, loadJob]);

  const currentStatus = getJobStatus(jobDetail, trackedSubmission);

  useEffect(() => {
    if (currentStatus !== "queued" && currentStatus !== "running") {
      setCancellingJob(false);
    }
  }, [currentStatus]);

  useEffect(() => {
    if (!jobIdFromRoute || (currentStatus !== "queued" && currentStatus !== "running")) {
      pollingInFlightRef.current = false;
      return;
    }

    let cancelled = false;
    const poll = async () => {
      if (cancelled || pollingInFlightRef.current) {
        return;
      }

      pollingInFlightRef.current = true;
      try {
        await loadJob(jobIdFromRoute);
      } finally {
        pollingInFlightRef.current = false;
      }
    };

    void poll();
    const intervalId = window.setInterval(() => {
      void poll();
    }, POLL_INTERVAL_MS);

    return () => {
      cancelled = true;
      pollingInFlightRef.current = false;
      window.clearInterval(intervalId);
    };
  }, [currentStatus, jobIdFromRoute, loadJob]);

  useEffect(() => {
    const previousStatus = previousStatusRef.current;
    previousStatusRef.current = currentStatus;

    if (!jobIdFromRoute || !currentStatus) {
      return;
    }

    const transitionedToTerminal =
      (previousStatus === "queued" || previousStatus === "running") &&
      (currentStatus === "succeeded" || currentStatus === "failed" || currentStatus === "cancelled");

    if (!transitionedToTerminal || finalSyncJobIdRef.current === jobIdFromRoute) {
      return;
    }

    finalSyncJobIdRef.current = jobIdFromRoute;
    void loadJob(jobIdFromRoute);
  }, [currentStatus, jobIdFromRoute, loadJob]);

  const elapsedAnchorMs = useMemo(() => {
    if (!jobDetail) {
      return null;
    }

    const anchor = jobDetail.started_at ?? jobDetail.created_at;
    if (!anchor) {
      return null;
    }

    return parseServerTimestamp(anchor);
  }, [jobDetail]);

  useEffect(() => {
    if (!elapsedAnchorMs || (currentStatus !== "queued" && currentStatus !== "running")) {
      setElapsedMs(null);
      return;
    }

    const updateElapsed = () => {
      setElapsedMs(Math.max(0, Date.now() - elapsedAnchorMs));
    };

    updateElapsed();
    const intervalId = window.setInterval(updateElapsed, 1000);

    return () => window.clearInterval(intervalId);
  }, [currentStatus, elapsedAnchorMs]);

  const annotatedImagePath = jobDetail?.result?.image_refs.find((item) => item.kind === "annotated")?.path ?? null;

  useEffect(() => {
    let cancelled = false;

    if (!authState || !jobDetail?.job_id || currentStatus !== "succeeded") {
      setAnnotatedImageLoading(false);
      setAnnotatedImageError(null);
      updateAnnotatedImageUrl(null);
      return;
    }

    setAnnotatedImageLoading(true);
    setAnnotatedImageError(null);

    const fetchImage = async () => {
      try {
        const imageBlob = await getInferenceJobImage(authState.accessToken, jobDetail.job_id, "annotated");
        if (cancelled) {
          return;
        }

        const nextUrl = URL.createObjectURL(imageBlob);
        updateAnnotatedImageUrl(nextUrl);
      } catch (err) {
        if (cancelled) {
          return;
        }

        updateAnnotatedImageUrl(null);
        if (err instanceof ApiClientError) {
          setAnnotatedImageError(err.message);
        } else {
          setAnnotatedImageError("Unable to load annotated image.");
        }
      } finally {
        if (!cancelled) {
          setAnnotatedImageLoading(false);
        }
      }
    };

    void fetchImage();

    return () => {
      cancelled = true;
    };
  }, [authState, currentStatus, jobDetail?.job_id, updateAnnotatedImageUrl]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!authState || !selectedFile || !selectedModelId) {
      return;
    }

    setSubmitting(true);
    setSubmissionError(null);
    setJobError(null);
    setJobDetail(null);
    setModelSelectionNotice(null);

    try {
      const response = await createInferenceJob(authState.accessToken, {
        modelId: selectedModelId,
        image: selectedFile,
      });
      setTrackedSubmission(response);
      setSearchParams({ jobId: response.job_id });
    } catch (err) {
      if (err instanceof ApiClientError) {
        setSubmissionError(err.message);
      } else {
        setSubmissionError("Unable to submit the image for inference.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  async function handleCancelJob() {
    const activeJobId = jobDetail?.job_id ?? trackedSubmission?.job_id ?? null;
    if (!authState || !activeJobId || (currentStatus !== "queued" && currentStatus !== "running")) {
      return;
    }

    setCancellingJob(true);
    setJobError(null);

    try {
      const response = await cancelInferenceJob(authState.accessToken, activeJobId);
      setTrackedSubmission((current) => ({
        job_id: response.job_id,
        status: response.status,
        model_id: current?.model_id ?? jobDetail?.model_id ?? selectedModelId,
        engine_id: current?.engine_id ?? jobDetail?.engine_id ?? "unknown-engine",
      }));
      await loadJob(activeJobId);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setJobError(err.message);
      } else {
        setJobError("Unable to cancel inference job.");
      }
    } finally {
      setCancellingJob(false);
    }
  }

  function handleResetWorkflow() {
    activeJobIdRef.current = null;
    pollingInFlightRef.current = false;
    setSelectedFile(null);
    setSubmissionError(null);
    setJobError(null);
    setTrackedSubmission(null);
    setJobDetail(null);
    setModelSelectionNotice(null);
    setCancellingJob(false);
    previousStatusRef.current = null;
    finalSyncJobIdRef.current = null;
    setSearchParams({});
  }

  const resolvedJobId = jobDetail?.job_id ?? trackedSubmission?.job_id ?? null;
  const resolvedModelId = (jobDetail?.model_id ?? trackedSubmission?.model_id ?? selectedModelId) || "Not selected";
  const resolvedEngineId = jobDetail?.engine_id ?? trackedSubmission?.engine_id ?? "Not available";
  const selectedModel = models.find((model) => model.model_id === selectedModelId) ?? null;
  const selectedModelEngineFamily = selectedModel ? getEngineFamilyLabel(getEngineFamilyFromModel(selectedModel)) : null;
  const elapsedAnchorLabel = jobDetail?.started_at ? "started_at" : jobDetail?.created_at ? "created_at" : null;

  return (
    <AppShell
      title="Image Inference"
      description="Select an available model, upload a road image, and track the job through queued, running, and terminal states."
    >
      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)]">
        <section className="rounded-2xl bg-white p-5 shadow sm:p-6">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Submit a job</h2>
              <p className="mt-1 text-sm text-slate-600">
                Supported model presets come from the backend model registry.
              </p>
            </div>
            <button
              className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
              onClick={handleResetWorkflow}
              type="button"
            >
              Clear state
            </button>
          </div>

          <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
            <label className="block text-sm font-medium text-slate-700">
              Engine family
              <select
                className="mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2"
                disabled={modelsLoading || submitting}
                onChange={(event) => {
                  setModelSelectionNotice(null);
                  setSelectedEngineFamily(event.target.value as EngineFamily);
                }}
                value={selectedEngineFamily}
              >
                {ENGINE_FAMILY_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="block text-sm font-medium text-slate-700">
              Model
              <select
                className="mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2"
                disabled={modelsLoading || submitting || filteredModels.length === 0}
                onChange={(event) => {
                  setSelectedModelId(event.target.value);
                }}
                value={selectedModelId}
              >
                {modelsLoading ? <option>Loading models...</option> : null}
                {!modelsLoading && filteredModels.length === 0 ? <option>No models for selected engine family</option> : null}
                {groupedFilteredModels.map((group) => (
                  <optgroup key={group.key} label={group.label}>
                    {group.items.map((model) => (
                      <option key={model.model_id} value={model.model_id}>
                        {model.display_name} ({model.model_id})
                      </option>
                    ))}
                  </optgroup>
                ))}
              </select>
            </label>

            {modelSelectionNotice ? (
              <p className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
                {modelSelectionNotice}
              </p>
            ) : null}

            {selectedModel ? (
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
                <p className="text-sm font-semibold text-slate-900">{selectedModel.display_name}</p>
                <p className="mt-1 text-xs text-slate-500">Model ID: {selectedModel.model_id}</p>
                <p className="mt-2 text-sm text-slate-700">{selectedModel.description}</p>
                <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500">
                  <span>Engine family: {selectedModelEngineFamily}</span>
                  <span>Engine: {selectedModel.engine_id}</span>
                  <span>Runtime: {selectedModel.runtime_type}</span>
                  <span>Status: {selectedModel.status}</span>
                </div>
                {selectedModel.performance_notes ? (
                  <p className="mt-2 text-xs text-slate-500">Performance note: {selectedModel.performance_notes}</p>
                ) : null}
              </div>
            ) : null}

            <label className="block text-sm font-medium text-slate-700">
              Image
              <input
                accept="image/*"
                className="mt-1 block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
                disabled={submitting}
                onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
                type="file"
              />
            </label>

            {!selectedFile ? (
              <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-sm text-slate-500">
                No image selected yet. Choose a file to enable submission.
              </div>
            ) : (
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="text-sm font-medium text-slate-900">{selectedFile.name}</p>
                    <p className="text-xs text-slate-500">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
                  </div>
                  <button
                    className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-white"
                    onClick={() => setSelectedFile(null)}
                    type="button"
                  >
                    Remove file
                  </button>
                </div>
                {previewUrl ? (
                  <img
                    alt="Selected upload preview"
                    className="mt-4 max-h-72 w-full rounded-xl border border-slate-200 object-contain bg-white"
                    src={previewUrl}
                  />
                ) : null}
              </div>
            )}

            {modelsError ? <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{modelsError}</p> : null}
            {submissionError ? <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{submissionError}</p> : null}

            <button
              className="w-full rounded-md bg-brand-500 px-4 py-2 font-medium text-white hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={submitting || modelsLoading || !selectedFile || !selectedModelId}
              type="submit"
            >
              {submitting ? "Submitting..." : "Submit inference job"}
            </button>
          </form>
        </section>

        <section className="space-y-6">
          <div className="rounded-2xl bg-white p-5 shadow sm:p-6">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <h2 className="text-lg font-semibold text-slate-900">Job status</h2>
                <p className="mt-1 text-sm text-slate-600">
                  Polling continues automatically while the job is queued or running.
                </p>
              </div>

              {currentStatus ? <StatusBadge status={currentStatus} /> : null}
            </div>

            {!resolvedJobId ? (
              <div className="mt-6 rounded-xl border border-dashed border-slate-300 bg-slate-50 px-4 py-10 text-sm text-slate-500">
                No active job selected. Submit an image or open a previous result from{" "}
                <Link className="font-medium text-brand-700" to="/history">
                  history
                </Link>
                .
              </div>
            ) : (
              <div className="mt-6 space-y-4">
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="rounded-xl border border-slate-200 p-4">
                    <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Job ID</p>
                    <p className="mt-2 break-all text-sm text-slate-900">{resolvedJobId}</p>
                  </div>
                  <div className="rounded-xl border border-slate-200 p-4">
                    <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Model / Engine</p>
                    <p className="mt-2 text-sm text-slate-900">{resolvedModelId}</p>
                    <p className="mt-1 text-xs text-slate-500">{resolvedEngineId}</p>
                  </div>
                </div>

                <div className="grid gap-3 sm:grid-cols-3">
                  <div className="rounded-xl bg-slate-50 p-4">
                    <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Created</p>
                    <p className="mt-2 text-sm text-slate-900">{formatTimestamp(jobDetail?.created_at ?? null)}</p>
                  </div>
                  <div className="rounded-xl bg-slate-50 p-4">
                    <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Started</p>
                    <p className="mt-2 text-sm text-slate-900">{formatTimestamp(jobDetail?.started_at ?? null)}</p>
                  </div>
                  <div className="rounded-xl bg-slate-50 p-4">
                    <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Finished</p>
                    <p className="mt-2 text-sm text-slate-900">{formatTimestamp(jobDetail?.finished_at ?? null)}</p>
                  </div>
                </div>

                {currentStatus === "queued" || currentStatus === "running" ? (
                  <div className="rounded-xl border border-sky-200 bg-sky-50 px-4 py-3 text-sm text-sky-800">
                    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                      <div>
                        <p>
                          Job is currently <span className="font-semibold">{currentStatus}</span>. The page will keep polling
                          until it reaches a terminal state.
                        </p>
                        <p className="mt-2 text-xs font-medium uppercase tracking-wide text-sky-700">Elapsed (live)</p>
                        <p className="mt-1 text-lg font-semibold text-sky-900">{formatElapsed(elapsedMs)}</p>
                        <p className="mt-1 text-xs text-sky-700">
                          Source timestamp: {elapsedAnchorLabel ?? "waiting for server timestamps"}
                        </p>
                      </div>

                      <button
                        className="rounded-md border border-sky-300 px-4 py-2 text-sm font-medium text-sky-900 hover:bg-sky-100 disabled:cursor-not-allowed disabled:opacity-60"
                        disabled={cancellingJob}
                        onClick={() => void handleCancelJob()}
                        type="button"
                      >
                        {cancellingJob ? "Cancelling..." : "Cancel job"}
                      </button>
                    </div>
                  </div>
                ) : null}

                {currentStatus === "failed" ? (
                  <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
                    <p className="font-semibold">{jobDetail?.error?.code ?? "ENGINE_EXECUTION_FAILED"}</p>
                    <p className="mt-1">{jobDetail?.error?.message ?? "Inference job failed."}</p>
                  </div>
                ) : null}

                {currentStatus === "cancelled" ? (
                  <div className="rounded-xl border border-slate-300 bg-slate-100 px-4 py-3 text-sm text-slate-800">
                    <p className="font-semibold">Job cancelled</p>
                    <p className="mt-1">Inference processing was cancelled before completion.</p>
                  </div>
                ) : null}

                {jobError ? <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{jobError}</p> : null}
              </div>
            )}
          </div>

          {currentStatus === "succeeded" && jobDetail?.result ? (
            <>
              <div className="rounded-2xl bg-white p-5 shadow sm:p-6">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <h2 className="text-lg font-semibold text-slate-900">Result metadata</h2>
                    <p className="mt-1 text-sm text-slate-600">
                      Detection counts and image references returned by the completed job.
                    </p>
                  </div>

                  <Link
                    className="rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                    to="/history"
                  >
                    Open history
                  </Link>
                </div>

                <div className="mt-6 grid gap-3 sm:grid-cols-3">
                  <div className="rounded-xl bg-slate-50 p-4">
                    <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Detections</p>
                    <p className="mt-2 text-xl font-semibold text-slate-900">{jobDetail.result.detections.length}</p>
                  </div>
                  <div className="rounded-xl bg-slate-50 p-4">
                    <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Duration</p>
                    <p className="mt-2 text-xl font-semibold text-slate-900">
                      {formatDuration(jobDetail.result.duration_ms)}
                    </p>
                  </div>
                  <div className="rounded-xl bg-slate-50 p-4">
                    <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Image refs</p>
                    <p className="mt-2 text-xl font-semibold text-slate-900">{jobDetail.result.image_refs.length}</p>
                  </div>
                </div>

                <div className="mt-6 rounded-xl border border-slate-200 p-4">
                  <h3 className="text-sm font-semibold text-slate-900">Annotated image</h3>
                  {annotatedImageUrl ? (
                    <img
                      alt="Annotated inference result"
                      className="mt-4 max-h-[28rem] w-full rounded-xl border border-slate-200 object-contain bg-slate-50"
                      src={annotatedImageUrl}
                    />
                  ) : null}

                  {!annotatedImageUrl && annotatedImageLoading ? (
                    <p className="mt-4 text-sm text-slate-600">Loading annotated image...</p>
                  ) : null}

                  {!annotatedImageUrl && !annotatedImageLoading && annotatedImageError ? (
                    <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
                      <p>Unable to load annotated image from the authenticated image endpoint: {annotatedImageError}</p>
                      {annotatedImagePath ? (
                        <p className="mt-1 break-all">
                          Backend path: <span className="font-medium">{annotatedImagePath}</span>
                        </p>
                      ) : null}
                    </div>
                  ) : null}

                  {!annotatedImageUrl && !annotatedImageLoading && !annotatedImageError && annotatedImagePath ? (
                    <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
                      Annotated image is unavailable to render. Backend path:{" "}
                      <span className="break-all font-medium">{annotatedImagePath}</span>
                    </div>
                  ) : null}

                  {!annotatedImageUrl && !annotatedImageLoading && !annotatedImageError && !annotatedImagePath ? (
                    <p className="mt-4 text-sm text-slate-500">No annotated image reference was returned for this job.</p>
                  ) : null}
                </div>
              </div>

              <div className="rounded-2xl bg-white p-5 shadow sm:p-6">
                <h2 className="text-lg font-semibold text-slate-900">Detections</h2>
                <p className="mt-1 text-sm text-slate-600">Normalized detection output from the backend job detail API.</p>

                <div className="mt-6 overflow-x-auto">
                  <table className="min-w-full divide-y divide-slate-200 text-sm">
                    <thead>
                      <tr className="text-left text-slate-500">
                        <th className="pb-3 pr-4 font-medium">Label</th>
                        <th className="pb-3 pr-4 font-medium">Confidence</th>
                        <th className="pb-3 pr-4 font-medium">x1</th>
                        <th className="pb-3 pr-4 font-medium">y1</th>
                        <th className="pb-3 pr-4 font-medium">x2</th>
                        <th className="pb-3 font-medium">y2</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 text-slate-700">
                      {jobDetail.result.detections.map((detection, index) => (
                        <tr key={`${detection.label}-${index}`}>
                          <td className="py-3 pr-4 font-medium text-slate-900">{detection.label}</td>
                          <td className="py-3 pr-4">{formatConfidence(detection.confidence)}</td>
                          <td className="py-3 pr-4">{detection.bbox.x1.toFixed(1)}</td>
                          <td className="py-3 pr-4">{detection.bbox.y1.toFixed(1)}</td>
                          <td className="py-3 pr-4">{detection.bbox.x2.toFixed(1)}</td>
                          <td className="py-3">{detection.bbox.y2.toFixed(1)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          ) : null}
        </section>
      </div>
    </AppShell>
  );
}
