import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { HistoryListResponse, ModelListResponse } from "../types";
import { HistoryPage } from "./HistoryPage";

const AUTH_STATE = {
  accessToken: "token-123",
  refreshToken: "refresh-123",
  user: {
    id: 1,
    email: "history-user@example.com",
    role: "user" as const,
  },
};

const mocks = vi.hoisted(() => ({
  listModels: vi.fn(),
  getHistory: vi.fn(),
  deleteHistoryItem: vi.fn(),
  clearHistory: vi.fn(),
  confirm: vi.fn(),
}));

vi.mock("../api/inference", () => ({
  listModels: mocks.listModels,
  getHistory: mocks.getHistory,
  deleteHistoryItem: mocks.deleteHistoryItem,
  clearHistory: mocks.clearHistory,
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

function makeHistoryResponse(partial: Partial<HistoryListResponse>): HistoryListResponse {
  return {
    items: [],
    page: 1,
    page_size: 10,
    total: 0,
    ...partial,
  };
}

function renderHistoryPage(route = "/history") {
  render(
    <MemoryRouter initialEntries={[route]}>
      <Routes>
        <Route element={<HistoryPage />} path="/history" />
      </Routes>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.stubGlobal("confirm", mocks.confirm);

  const modelResponse: ModelListResponse = {
    items: [
      {
        model_id: "rddc2020-imsc-last95",
        engine_id: "rddc2020-cli",
        status: "active",
        performance_notes: null,
        display_name: "IMSC Last95",
        description: "Primary model",
        runtime_type: "cli",
      },
    ],
  };

  mocks.listModels.mockResolvedValue(modelResponse);
  mocks.clearHistory.mockResolvedValue({ message: "History cleared.", deleted_count: 0 });
});

describe("HistoryPage", () => {
  it("renders picture title from original filename and model display name", async () => {
    mocks.getHistory.mockResolvedValue(
      makeHistoryResponse({
        total: 1,
        items: [
          {
            job_id: "job-1",
            model_id: "rddc2020-imsc-last95",
            engine_id: "rddc2020-cli",
            status: "succeeded",
            timestamp: "2026-03-24T00:00:00Z",
            original_filename: "road_001.png",
            defect_count: 1,
            max_confidence: 0.8,
          },
        ],
      }),
    );

    renderHistoryPage();

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: "road_001.png" })).toBeInTheDocument();
    });

    expect(screen.getByText("Model: IMSC Last95")).toBeInTheDocument();
  });

  it("uses default page size/sort and resets to page 1 when page size changes", async () => {
    mocks.getHistory.mockImplementation(
      async (
        _token: string,
        query: { page?: number; pageSize?: number; sortBy?: string; sortOrder?: string },
      ) => {
        const page = query.page ?? 1;
        const pageSize = query.pageSize ?? 10;

        return makeHistoryResponse({
          page,
          page_size: pageSize,
          total: 21,
          items: [
            {
              job_id: `job-page-${page}`,
              model_id: "rddc2020-imsc-last95",
              engine_id: "rddc2020-cli",
              status: "succeeded",
              timestamp: "2026-03-24T00:00:00Z",
              original_filename: `page-${page}.png`,
              defect_count: 1,
              max_confidence: 0.8,
            },
          ],
        });
      },
    );

    renderHistoryPage("/history?page=3");

    await waitFor(() => {
      expect(mocks.getHistory.mock.calls).toContainEqual([
        "token-123",
        {
          page: 3,
          pageSize: 10,
          modelId: undefined,
          sortBy: "time",
          sortOrder: "desc",
        },
      ]);
    });

    fireEvent.change(screen.getByLabelText("Page size"), { target: { value: "50" } });

    await waitFor(() => {
      expect(mocks.getHistory.mock.calls).toContainEqual([
        "token-123",
        {
          page: 1,
          pageSize: 50,
          modelId: undefined,
          sortBy: "time",
          sortOrder: "desc",
        },
      ]);
    });
  });

  it("updates sort controls and keeps query state in API calls", async () => {
    mocks.getHistory.mockImplementation(
      async (
        _token: string,
        query: { page?: number; pageSize?: number; sortBy?: string; sortOrder?: string },
      ) => {
        const page = query.page ?? 1;
        const pageSize = query.pageSize ?? 10;

        return makeHistoryResponse({
          page,
          page_size: pageSize,
          total: 2,
          items: [
            {
              job_id: `job-page-${page}`,
              model_id: "rddc2020-imsc-last95",
              engine_id: "rddc2020-cli",
              status: "succeeded",
              timestamp: "2026-03-24T00:00:00Z",
              original_filename: `sort-${page}.png`,
              defect_count: 1,
              max_confidence: 0.8,
            },
          ],
        });
      },
    );

    renderHistoryPage("/history?page=2");

    await waitFor(() => {
      expect(mocks.getHistory.mock.calls).toContainEqual([
        "token-123",
        {
          page: 2,
          pageSize: 10,
          modelId: undefined,
          sortBy: "time",
          sortOrder: "desc",
        },
      ]);
    });

    fireEvent.change(screen.getByLabelText("Sort by"), { target: { value: "id" } });

    await waitFor(() => {
      expect(mocks.getHistory.mock.calls).toContainEqual([
        "token-123",
        {
          page: 1,
          pageSize: 10,
          modelId: undefined,
          sortBy: "id",
          sortOrder: "desc",
        },
      ]);
    });

    fireEvent.change(screen.getByLabelText("Order"), { target: { value: "asc" } });

    await waitFor(() => {
      expect(mocks.getHistory.mock.calls).toContainEqual([
        "token-123",
        {
          page: 1,
          pageSize: 10,
          modelId: undefined,
          sortBy: "id",
          sortOrder: "asc",
        },
      ]);
    });
  });

  it("deletes one item and moves to previous page when the current page becomes empty", async () => {
    mocks.confirm.mockReturnValue(true);

    let deleted = false;
    mocks.deleteHistoryItem.mockImplementation(async () => {
      deleted = true;
      return {
        message: "History item deleted.",
        job_id: "job-delete",
      };
    });

    mocks.getHistory.mockImplementation(
      async (
        _token: string,
        query: { page?: number; pageSize?: number; sortBy?: string; sortOrder?: string },
      ) => {
        const page = query.page ?? 1;
        const pageSize = query.pageSize ?? 10;

        if (page === 2 && !deleted) {
          return makeHistoryResponse({
            page: 2,
            page_size: pageSize,
            total: 11,
            items: [
              {
                job_id: "job-delete",
                model_id: "rddc2020-imsc-last95",
                engine_id: "rddc2020-cli",
                status: "succeeded",
                timestamp: "2026-03-24T00:00:00Z",
                original_filename: "delete-me.png",
                defect_count: 2,
                max_confidence: 0.7,
              },
            ],
          });
        }

        if (page === 2 && deleted) {
          return makeHistoryResponse({
            page: 2,
            page_size: pageSize,
            total: 10,
            items: [],
          });
        }

        return makeHistoryResponse({
          page: 1,
          page_size: pageSize,
          total: 10,
          items: [
            {
              job_id: "job-remaining",
              model_id: "rddc2020-imsc-last95",
              engine_id: "rddc2020-cli",
              status: "succeeded",
              timestamp: "2026-03-24T00:00:00Z",
              original_filename: "remaining.png",
              defect_count: 1,
              max_confidence: 0.6,
            },
          ],
        });
      },
    );

    renderHistoryPage("/history?page=2");

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Delete" })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Delete" }));

    await waitFor(() => {
      expect(mocks.deleteHistoryItem).toHaveBeenCalledWith("token-123", "job-delete");
    });

    await waitFor(() => {
      expect(mocks.getHistory.mock.calls).toContainEqual([
        "token-123",
        {
          page: 2,
          pageSize: 10,
          modelId: undefined,
          sortBy: "time",
          sortOrder: "desc",
        },
      ]);
      expect(mocks.getHistory.mock.calls).toContainEqual([
        "token-123",
        {
          page: 1,
          pageSize: 10,
          modelId: undefined,
          sortBy: "time",
          sortOrder: "desc",
        },
      ]);
    });
  });
});
