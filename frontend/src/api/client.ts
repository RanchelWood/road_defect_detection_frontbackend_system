import type { ApiEnvelope } from "../types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
let unauthorizedHandler: (() => void) | null = null;

export class ApiClientError extends Error {
  public readonly code: string;
  public readonly status: number;

  constructor(message: string, code: string, status: number) {
    super(message);
    this.name = "ApiClientError";
    this.code = code;
    this.status = status;
  }
}

async function parseJson<T>(response: Response): Promise<ApiEnvelope<T>> {
  const payload = (await response.json()) as ApiEnvelope<T>;
  return payload;
}

async function parseErrorResponse(response: Response): Promise<{ code: string; message: string }> {
  const contentType = response.headers.get("content-type") ?? "";

  if (contentType.includes("application/json")) {
    try {
      const payload = (await response.json()) as ApiEnvelope<unknown>;
      if (payload.success === false) {
        return {
          code: payload.error.code,
          message: payload.error.message,
        };
      }
    } catch {
      // Ignore JSON parsing failures and fall back to a generic error.
    }
  }

  return {
    code: "HTTP_ERROR",
    message: "Request failed",
  };
}

export function setUnauthorizedHandler(handler: (() => void) | null) {
  unauthorizedHandler = handler;
}

async function requestJson<TResponse>(
  path: string,
  init: RequestInit,
  token?: string,
): Promise<TResponse> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      ...(init.headers ?? {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });

  const payload = await parseJson<TResponse>(response);

  if (response.status === 401 && token) {
    unauthorizedHandler?.();
  }

  if (!response.ok || payload.success === false) {
    const code = payload.success === false ? payload.error.code : "HTTP_ERROR";
    const message = payload.success === false ? payload.error.message : "Request failed";
    throw new ApiClientError(message, code, response.status);
  }

  return payload.data;
}

export async function postJson<TResponse, TBody>(
  path: string,
  body: TBody,
  token?: string,
): Promise<TResponse> {
  return requestJson<TResponse>(
    path,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    },
    token,
  );
}

export async function postFormData<TResponse>(
  path: string,
  body: FormData,
  token: string,
): Promise<TResponse> {
  return requestJson<TResponse>(
    path,
    {
      method: "POST",
      body,
    },
    token,
  );
}

export async function getJson<TResponse>(path: string, token?: string): Promise<TResponse> {
  return requestJson<TResponse>(
    path,
    {
      method: "GET",
    },
    token,
  );
}

export async function getBlob(path: string, token: string): Promise<Blob> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (response.status === 401) {
    unauthorizedHandler?.();
  }

  if (!response.ok) {
    const parsedError = await parseErrorResponse(response);
    throw new ApiClientError(parsedError.message, parsedError.code, response.status);
  }

  return response.blob();
}
