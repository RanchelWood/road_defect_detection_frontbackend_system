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