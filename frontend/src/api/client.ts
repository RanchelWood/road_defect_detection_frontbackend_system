import type { ApiEnvelope } from "../types";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

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

export async function postJson<TResponse, TBody>(
  path: string,
  body: TBody,
  token?: string,
): Promise<TResponse> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body),
  });

  const payload = await parseJson<TResponse>(response);

  if (!response.ok || payload.success === false) {
    const code = payload.success === false ? payload.error.code : "HTTP_ERROR";
    const message = payload.success === false ? payload.error.message : "Request failed";
    throw new ApiClientError(message, code, response.status);
  }

  return payload.data;
}

export async function getJson<TResponse>(path: string, token?: string): Promise<TResponse> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "GET",
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });

  const payload = await parseJson<TResponse>(response);

  if (!response.ok || payload.success === false) {
    const code = payload.success === false ? payload.error.code : "HTTP_ERROR";
    const message = payload.success === false ? payload.error.message : "Request failed";
    throw new ApiClientError(message, code, response.status);
  }

  return payload.data;
}