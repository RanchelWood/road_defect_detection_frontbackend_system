import { getJson, postJson } from "./client";
import type { AuthPayload } from "../types";

type RegisterRequest = {
  email: string;
  password: string;
};

type LoginRequest = {
  email: string;
  password: string;
};

type RefreshRequest = {
  refresh_token: string;
};

type LogoutRequest = {
  refresh_token: string;
};

export function register(payload: RegisterRequest): Promise<AuthPayload> {
  return postJson<AuthPayload, RegisterRequest>("/auth/register", payload);
}

export function login(payload: LoginRequest): Promise<AuthPayload> {
  return postJson<AuthPayload, LoginRequest>("/auth/login", payload);
}

export function refresh(refreshToken: string): Promise<AuthPayload> {
  return postJson<AuthPayload, RefreshRequest>("/auth/refresh", {
    refresh_token: refreshToken,
  });
}

export function logout(refreshToken: string): Promise<{ message: string }> {
  return postJson<{ message: string }, LogoutRequest>("/auth/logout", {
    refresh_token: refreshToken,
  });
}

export function health(): Promise<{ status: string }> {
  return getJson<{ status: string }>("/health");
}