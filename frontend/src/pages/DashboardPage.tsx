import { useState } from "react";
import { Link } from "react-router-dom";

import { health } from "../api/auth";
import { ApiClientError } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { AppShell } from "../components/AppShell";

export function DashboardPage() {
  const { authState } = useAuth();

  const [healthStatus, setHealthStatus] = useState<string>("Not checked");
  const [loadingHealth, setLoadingHealth] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleCheckHealth() {
    setLoadingHealth(true);
    setError(null);
    try {
      const response = await health();
      setHealthStatus(response.status);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message);
      } else {
        setError("Failed to check backend health.");
      }
    } finally {
      setLoadingHealth(false);
    }
  }

  if (!authState) {
    return null;
  }

  return (
    <AppShell
      title="Dashboard"
      description="Monitor connectivity, check your active session, and move into the inference workflow."
    >
      <div className="grid gap-4 md:grid-cols-2">
        <section className="rounded-xl bg-white p-6 shadow">
          <h2 className="mb-3 text-lg font-semibold text-slate-900">Workflow</h2>
          <p className="mb-4 text-sm text-slate-600">
            Submit a new image for inference or review previous jobs from your history.
          </p>
          <div className="flex flex-col gap-3 sm:flex-row">
            <Link
              className="rounded-md bg-brand-500 px-4 py-2 text-center font-medium text-white hover:bg-brand-700"
              to="/inference"
            >
              Open inference
            </Link>
            <Link
              className="rounded-md border border-slate-300 px-4 py-2 text-center font-medium text-slate-700 hover:bg-slate-50"
              to="/history"
            >
              View history
            </Link>
          </div>
        </section>

        <section className="rounded-xl bg-white p-6 shadow">
          <h2 className="mb-3 text-lg font-semibold text-slate-900">Backend Health</h2>
          <p className="mb-4 text-sm text-slate-600">Current status: {healthStatus}</p>
          <button
            className="rounded-md bg-brand-500 px-4 py-2 font-medium text-white hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-60"
            onClick={handleCheckHealth}
            disabled={loadingHealth}
          >
            {loadingHealth ? "Checking..." : "Check /health"}
          </button>
        </section>

        <section className="rounded-xl bg-white p-6 shadow md:col-span-2">
          <h2 className="mb-3 text-lg font-semibold text-slate-900">Session</h2>
          <p className="mb-2 text-sm text-slate-600">Role: {authState.user.role}</p>
          <p className="mb-4 break-all text-xs text-slate-500">Access token: {authState.accessToken}</p>
          <p className="text-sm text-slate-600">Use the navigation above to move between dashboard, inference, and history.</p>
        </section>
      </div>

      {error ? <p className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}
    </AppShell>
  );
}
