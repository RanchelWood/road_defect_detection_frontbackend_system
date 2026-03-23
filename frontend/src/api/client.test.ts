import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiClientError, getBlob, getJson, postJson, setUnauthorizedHandler } from "./client";

function successEnvelope(data: unknown) {
  return {
    success: true,
    data,
    meta: {
      request_id: "req-test",
      timestamp: "2026-03-23T00:00:00Z",
    },
  };
}

afterEach(() => {
  vi.restoreAllMocks();
  setUnauthorizedHandler(null);
});

describe("api/client", () => {
  it("postJson sends json body and returns envelope data", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify(successEnvelope({ token: "abc" })), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );

    const data = await postJson<{ token: string }, { email: string }>("/auth/login", { email: "a@b.com" });

    expect(data).toEqual({ token: "abc" });
    expect(fetchMock).toHaveBeenCalledOnce();

    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(init.method).toBe("POST");
    expect(init.headers).toMatchObject({ "Content-Type": "application/json" });
    expect(init.body).toBe(JSON.stringify({ email: "a@b.com" }));
  });

  it("getJson triggers unauthorized handler on 401 and throws ApiClientError", async () => {
    const unauthorized = vi.fn();
    setUnauthorizedHandler(unauthorized);

    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          success: false,
          error: { code: "AUTH_TOKEN_INVALID", message: "Invalid token", details: {} },
          meta: { request_id: "req-401", timestamp: "2026-03-23T00:00:00Z" },
        }),
        {
          status: 401,
          headers: { "Content-Type": "application/json" },
        },
      ),
    );

    await expect(getJson("/models", "token-123")).rejects.toBeInstanceOf(ApiClientError);
    expect(unauthorized).toHaveBeenCalledTimes(1);
  });

  it("getBlob parses error envelope and throws ApiClientError", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          success: false,
          error: { code: "IMAGE_NOT_FOUND", message: "Missing image", details: {} },
          meta: { request_id: "req-404", timestamp: "2026-03-23T00:00:00Z" },
        }),
        {
          status: 404,
          headers: { "Content-Type": "application/json" },
        },
      ),
    );

    await expect(getBlob("/inference/jobs/id/image/annotated", "token-abc")).rejects.toMatchObject({
      code: "IMAGE_NOT_FOUND",
      status: 404,
    });
  });
});
