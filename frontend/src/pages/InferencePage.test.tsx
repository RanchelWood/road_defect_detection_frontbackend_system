import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { InferenceJobDetail, InferenceJobStatus, ModelListResponse } from "../types";
import { InferencePage } from "./InferencePage";

const SELECTED_MODEL_STORAGE_KEY = "road_defect_selected_model_id";

const AUTH_STATE = {
  accessToken: "token-123",
  refreshToken: "refresh-123",
  user: {
    id: 1,
    email: "inference-user@example.com",
    role: "user" as const,
  },
};

const mocks = vi.hoisted(() => ({
  listModels: vi.fn(),
  createInferenceJob: vi.fn(),
  getInferenceJob: vi.fn(),
  getInferenceJobImage: vi.fn(),
  cancelInferenceJob: vi.fn(),
}));

vi.mock("../api/inference", () => ({
  listModels: mocks.listModels,
  createInferenceJob: mocks.createInferenceJob,
  getInferenceJob: mocks.getInferenceJob,
  getInferenceJobImage: mocks.getInferenceJobImage,
  cancelInferenceJob: mocks.cancelInferenceJob,
}));

vi.mock("../auth/AuthContext", () => ({
  useAuth: () => ({
    authState: AUTH_STATE,
  }),
}));

vi.mock("../components/AppShell", () => ({
  AppShell: ({ children }: { children: ReactNode }) => <div>{children}</div>,
}));

vi.mock("../components/StatusBadge", () => ({
  StatusBadge: ({ status }: { status: string }) => <span>{status}</span>,
}));

function renderInferencePage(route = "/inference") {
  render(
    <MemoryRouter initialEntries={[route]}>
      <Routes>
        <Route element={<InferencePage />} path="/inference" />
      </Routes>
    </MemoryRouter>,
  );
}

function makeJobDetail(status: InferenceJobStatus): InferenceJobDetail {
  const finishedAt = status === "cancelled" ? "2026-03-25T00:02:00Z" : null;

  return {
    job_id: "job-1",
    status,
    model_id: "model-a",
    engine_id: "engine-1",
    created_at: "2026-03-25T00:00:00Z",
    started_at: "2026-03-25T00:01:00Z",
    finished_at: finishedAt,
    result: null,
    error: null,
  };
}

beforeEach(() => {
  vi.clearAllMocks();
  localStorage.clear();

  const modelResponse: ModelListResponse = {
    items: [
      {
        model_id: "model-a",
        engine_id: "engine-1",
        status: "active",
        performance_notes: null,
        display_name: "Model A",
        description: "Primary model",
        runtime_type: "cli",
      },
      {
        model_id: "model-b",
        engine_id: "engine-1",
        status: "active",
        performance_notes: null,
        display_name: "Model B",
        description: "Secondary model",
        runtime_type: "cli",
      },
    ],
  };

  mocks.listModels.mockResolvedValue(modelResponse);
  mocks.getInferenceJobImage.mockRejectedValue(new Error("not used in these tests"));
});

describe("InferencePage", () => {
  it("restores selected model from localStorage and persists changes", async () => {
    localStorage.setItem(SELECTED_MODEL_STORAGE_KEY, "model-b");

    renderInferencePage();

    const modelSelect = (await screen.findByLabelText("Model")) as HTMLSelectElement;
    expect(modelSelect.value).toBe("model-b");

    fireEvent.change(modelSelect, { target: { value: "model-a" } });

    await waitFor(() => {
      expect(localStorage.getItem(SELECTED_MODEL_STORAGE_KEY)).toBe("model-a");
    });
  });

  it("falls back to first model when persisted model is unavailable", async () => {
    localStorage.setItem(SELECTED_MODEL_STORAGE_KEY, "unknown-model");

    renderInferencePage();

    const modelSelect = (await screen.findByLabelText("Model")) as HTMLSelectElement;
    expect(modelSelect.value).toBe("model-a");
  });

  it("allows cancelling a running job and shows cancelled state", async () => {
    let cancelled = false;

    mocks.getInferenceJob.mockImplementation(async () => makeJobDetail(cancelled ? "cancelled" : "running"));
    mocks.cancelInferenceJob.mockImplementation(async () => {
      cancelled = true;
      return {
        job_id: "job-1",
        status: "cancelled",
        message: "Job cancelled.",
      };
    });

    renderInferencePage("/inference?jobId=job-1");

    const cancelButton = await screen.findByRole("button", { name: "Cancel job" });
    fireEvent.click(cancelButton);

    await waitFor(() => {
      expect(mocks.cancelInferenceJob).toHaveBeenCalledWith("token-123", "job-1");
    });

    await waitFor(() => {
      expect(screen.getByText("Job cancelled")).toBeInTheDocument();
    });
  });
});
