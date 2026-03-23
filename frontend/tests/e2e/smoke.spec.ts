import { expect, test } from "@playwright/test";

const AUTH_STORAGE_KEY = "road_defect_auth";

const AUTH_STATE = {
  accessToken: "access-token",
  refreshToken: "refresh-token",
  user: {
    id: 1,
    email: "tester@example.com",
    role: "user",
    created_at: "2026-03-23T00:00:00Z",
  },
};

const ENVELOPE_META = {
  request_id: "req-e2e",
  timestamp: "2026-03-23T00:00:00Z",
};

function successEnvelope(data: unknown) {
  return {
    success: true,
    data,
    meta: ENVELOPE_META,
  };
}

const tinyPng = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/w8AAgMBgN6n4i8AAAAASUVORK5CYII=",
  "base64",
);

test("@smoke redirects unauthenticated users from protected routes", async ({ page }) => {
  await page.goto("/dashboard");

  await expect(page).toHaveURL(/\/login$/);
  await expect(page.getByRole("heading", { name: "Login" })).toBeVisible();
});

test("@smoke login navigates to dashboard and logout returns to login", async ({ page }) => {
  await page.route("**/auth/login", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(
        successEnvelope({
          access_token: AUTH_STATE.accessToken,
          refresh_token: AUTH_STATE.refreshToken,
          user: AUTH_STATE.user,
        }),
      ),
    });
  });

  await page.route("**/auth/logout", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(successEnvelope({ message: "Logged out" })),
    });
  });

  await page.goto("/login");
  await page.getByLabel("Email").fill("tester@example.com");
  await page.getByLabel("Password").fill("Password1");
  await page.getByRole("button", { name: "Login" }).click();

  await expect(page).toHaveURL(/\/dashboard$/);
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();

  await page.getByRole("button", { name: "Logout" }).click();
  await expect(page).toHaveURL(/\/login$/);
});

test("@smoke inference submit auto-updates to succeeded and renders result", async ({ page }) => {
  await page.addInitScript(
    ({ storageKey, state }) => {
      localStorage.setItem(storageKey, JSON.stringify(state));
    },
    { storageKey: AUTH_STORAGE_KEY, state: AUTH_STATE },
  );

  let pollCount = 0;

  await page.route("**/models", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(
        successEnvelope({
          items: [
            {
              model_id: "rddc2020-imsc-last95",
              engine_id: "rddc2020-cli",
              display_name: "IMSC Last95",
              description: "Smoke model",
              runtime_type: "cli",
              status: "active",
              performance_notes: "smoke",
            },
          ],
        }),
      ),
    });
  });

  await page.route("**/inference/jobs", async (route) => {
    if (route.request().method() !== "POST") {
      await route.fallback();
      return;
    }

    await route.fulfill({
      status: 202,
      contentType: "application/json",
      body: JSON.stringify(
        successEnvelope({
          job_id: "job-e2e-1",
          status: "queued",
          model_id: "rddc2020-imsc-last95",
          engine_id: "rddc2020-cli",
        }),
      ),
    });
  });

  await page.route("**/inference/jobs/job-e2e-1/image/annotated", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "image/png",
      body: tinyPng,
    });
  });

  await page.route("**/inference/jobs/job-e2e-1", async (route) => {
    pollCount += 1;

    const status = pollCount < 2 ? "running" : "succeeded";
    const result =
      status === "succeeded"
        ? {
            model_id: "rddc2020-imsc-last95",
            engine_id: "rddc2020-cli",
            duration_ms: 321,
            detections: [
              {
                label: "D00",
                confidence: 0.92,
                bbox: { x1: 10, y1: 20, x2: 30, y2: 40 },
              },
            ],
            image_refs: [
              { id: "orig-1", kind: "original", path: "D:/tmp/input.jpg" },
              { id: "ann-1", kind: "annotated", path: "D:/tmp/annotated.jpg" },
            ],
          }
        : null;

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(
        successEnvelope({
          job_id: "job-e2e-1",
          status,
          model_id: "rddc2020-imsc-last95",
          engine_id: "rddc2020-cli",
          created_at: "2026-03-23T00:00:00Z",
          started_at: "2026-03-23T00:00:01Z",
          finished_at: status === "succeeded" ? "2026-03-23T00:00:03Z" : null,
          result,
          error: null,
        }),
      ),
    });
  });

  await page.goto("/inference");
  await page.setInputFiles('input[type="file"]', {
    name: "road.jpg",
    mimeType: "image/jpeg",
    buffer: Buffer.from("fake-image"),
  });

  await page.getByRole("button", { name: "Submit inference job" }).click();

  await expect(page).toHaveURL(/\/inference\?jobId=job-e2e-1/);
  await expect(page.getByText("Result metadata")).toBeVisible({ timeout: 10000 });
  await expect(page.getByRole("heading", { name: "Detections" })).toBeVisible();
  await expect(page.getByText("D00")).toBeVisible();
});

