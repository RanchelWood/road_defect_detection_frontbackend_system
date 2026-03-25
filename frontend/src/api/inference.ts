import { deleteJson, getBlob, getJson, postFormData } from "./client";
import type {
  HistoryListResponse,
  InferenceJobDetail,
  InferenceJobSubmission,
  ModelListResponse,
} from "../types";

type HistoryQuery = {
  page?: number;
  pageSize?: number;
  modelId?: string;
};

type InferenceImageKind = "original" | "annotated";

type DeleteHistoryItemResponse = {
  message: string;
  job_id: string;
};

type ClearHistoryResponse = {
  message: string;
  deleted_count: number;
};

export function listModels(token: string): Promise<ModelListResponse> {
  return getJson<ModelListResponse>("/models", token);
}

export function createInferenceJob(
  token: string,
  payload: { modelId: string; image: File },
): Promise<InferenceJobSubmission> {
  const formData = new FormData();
  formData.set("model_id", payload.modelId);
  formData.set("image", payload.image);
  return postFormData<InferenceJobSubmission>("/inference/jobs", formData, token);
}

export function getInferenceJob(token: string, jobId: string): Promise<InferenceJobDetail> {
  return getJson<InferenceJobDetail>(`/inference/jobs/${jobId}`, token);
}

export function getInferenceJobImage(token: string, jobId: string, kind: InferenceImageKind): Promise<Blob> {
  return getBlob(`/inference/jobs/${jobId}/image/${kind}`, token);
}

export function getHistory(token: string, query: HistoryQuery): Promise<HistoryListResponse> {
  const params = new URLSearchParams();

  if (query.page) {
    params.set("page", String(query.page));
  }
  if (query.pageSize) {
    params.set("page_size", String(query.pageSize));
  }
  if (query.modelId) {
    params.set("model_id", query.modelId);
  }

  const suffix = params.toString() ? `?${params.toString()}` : "";
  return getJson<HistoryListResponse>(`/history${suffix}`, token);
}

export function deleteHistoryItem(token: string, jobId: string): Promise<DeleteHistoryItemResponse> {
  return deleteJson<DeleteHistoryItemResponse>(`/history/${jobId}`, token);
}

export function clearHistory(token: string): Promise<ClearHistoryResponse> {
  return deleteJson<ClearHistoryResponse>("/history", token);
}

