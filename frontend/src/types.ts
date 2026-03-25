export type ApiMeta = {
  request_id: string;
  timestamp: string;
};

export type ApiErrorBody = {
  code: string;
  message: string;
  details?: Record<string, unknown>;
};

export type ApiSuccess<T> = {
  success: true;
  data: T;
  meta: ApiMeta;
};

export type ApiFailure = {
  success: false;
  error: ApiErrorBody;
  meta: ApiMeta;
};

export type ApiEnvelope<T> = ApiSuccess<T> | ApiFailure;

export type UserPublic = {
  id: number;
  email: string;
  role: "admin" | "user";
};

export type AuthPayload = {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  expires_in: number;
  user: UserPublic;
};

export type ModelSummary = {
  model_id: string;
  engine_id: string;
  status: string;
  performance_notes: string | null;
  display_name: string;
  description: string;
  runtime_type: string;
};

export type ModelListResponse = {
  items: ModelSummary[];
};

export type InferenceJobStatus = "queued" | "running" | "succeeded" | "failed" | "cancelled";

export type InferenceJobSubmission = {
  job_id: string;
  status: InferenceJobStatus;
  model_id: string;
  engine_id: string;
};

export type DetectionBoundingBox = {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
};

export type Detection = {
  label: string;
  confidence: number | null;
  bbox: DetectionBoundingBox;
};

export type ResultImageRef = {
  id: string;
  kind: string;
  path: string;
};

export type InferenceResult = {
  model_id: string;
  engine_id: string;
  detections: Detection[];
  image_refs: ResultImageRef[];
  duration_ms: number;
};

export type InferenceJobDetail = {
  job_id: string;
  status: InferenceJobStatus;
  model_id: string;
  engine_id: string;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  result: InferenceResult | null;
  error: ApiErrorBody | null;
};

export type HistorySortBy = "time" | "id" | "name";
export type SortOrder = "asc" | "desc";

export type HistoryItem = {
  job_id: string;
  model_id: string;
  engine_id: string;
  status: InferenceJobStatus;
  timestamp: string;
  original_filename?: string | null;
  defect_count?: number;
  max_confidence?: number;
};

export type HistoryListResponse = {
  items: HistoryItem[];
  page: number;
  page_size: number;
  total: number;
};
