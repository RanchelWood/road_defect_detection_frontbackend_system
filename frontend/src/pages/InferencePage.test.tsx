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
    model_id: "rddc2020-imsc-last95",
    engine_id: "rddc2020-cli",
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
        model_id: "rddc2020-imsc-last95",
        engine_id: "rddc2020-cli",
        status: "active",
        performance_notes: "Stable baseline model",
        display_name: "RDDC2020 IMSC Last95",
        description: "RDDC2020 baseline model",
        runtime_type: "cli",
      },
      {
        model_id: "rddc2020-fast",
        engine_id: "rddc2020-cli",
        status: "active",
        performance_notes: null,
        display_name: "RDDC2020 Fast",
        description: "Faster RDDC2020 variant",
        runtime_type: "cli",
      },
      {
        model_id: "orddc2024-main",
        engine_id: "orddc2024-cli",
        status: "active",
        performance_notes: "Recommended for new uploads",
        display_name: "ORDDC2024 Main",
        description: "ORDDC2024 default model",
        runtime_type: "python",
      },
      {
        model_id: "orddc2024-accurate",
        engine_id: "orddc2024-cli",
        status: "active",
        performance_notes: null,
        display_name: "ORDDC2024 Accurate",
        description: "ORDDC2024 high-accuracy model",
        runtime_type: "python",
      },
    ],
  };

  mocks.listModels.mockResolvedValue(modelResponse);
  mocks.getInferenceJobImage.mockRejectedValue(new Error("not used in these tests"));
});

describe("InferencePage", () => {
  it("filters model options by engine family and keeps options grouped by engine", async () => {
    renderInferencePage();

    const modelSelect = (await screen.findByLabelText("Model")) as HTMLSelectElement;

    const initialGroups = Array.from(modelSelect.querySelectorAll("optgroup")).map((group) => group.label);
    expect(initialGroups).toContain("RDDC2020 (rddc2020-cli)");
    expect(initialGroups).toContain("ORDDC2024 (orddc2024-cli)");

    fireEvent.change(screen.getByLabelText("Engine family"), { target: { value: "orddc2024" } });

    await waitFor(() => {
      expect(modelSelect.value).toBe("orddc2024-main");
    });

    const optionValues = Array.from(modelSelect.querySelectorAll("option")).map((option) => option.value);
    expect(optionValues).toEqual(["orddc2024-main", "orddc2024-accurate"]);

    const filteredGroups = Array.from(modelSelect.querySelectorAll("optgroup")).map((group) => group.label);
    expect(filteredGroups).toEqual(["ORDDC2024 (orddc2024-cli)"]);
  });

  it("restores selected model from localStorage when available", async () => {
    localStorage.setItem(SELECTED_MODEL_STORAGE_KEY, "orddc2024-accurate");

    renderInferencePage();

    const modelSelect = (await screen.findByLabelText("Model")) as HTMLSelectElement;
    expect(modelSelect.value).toBe("orddc2024-accurate");
  });

  it("falls back safely when persisted/current model is unavailable after engine filter change", async () => {
    localStorage.setItem(SELECTED_MODEL_STORAGE_KEY, "rddc2020-fast");

    renderInferencePage();

    const modelSelect = (await screen.findByLabelText("Model")) as HTMLSelectElement;
    expect(modelSelect.value).toBe("rddc2020-fast");

    fireEvent.change(screen.getByLabelText("Engine family"), { target: { value: "orddc2024" } });

    await waitFor(() => {
      expect(modelSelect.value).toBe("orddc2024-main");
    });

    expect(localStorage.getItem(SELECTED_MODEL_STORAGE_KEY)).toBe("orddc2024-main");
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
