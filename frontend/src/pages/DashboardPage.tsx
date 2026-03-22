import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { health, logout } from "../api/auth";
import { ApiClientError } from "../api/client";
import { useAuth } from "../auth/AuthContext";

export function DashboardPage() {
  const navigate = useNavigate();
  const { authState, clearAuth } = useAuth();

  const [healthStatus, setHealthStatus] = useState<string>("Not checked");
  const [loadingHealth, setLoadingHealth] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loggingOut, setLoggingOut] = useState(false);

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

  async function handleLogout() {
    if (!authState) {
      return;
    }

    setLoggingOut(true);
    setError(null);

    try {
      await logout(authState.refreshToken);
    } catch {
      // Logout remains best-effort for local session cleanup.
    } finally {
      clearAuth();
      navigate("/login", { replace: true });
      setLoggingOut(false);
    }
  }

  if (!authState) {
    return null;
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-4xl flex-col p-6">
      <header className="mb-6 rounded-xl bg-white p-6 shadow">
        <h1 className="text-2xl font-semibold text-slate-900">Dashboard</h1>
        <p className="mt-2 text-slate-600">Signed in as {authState.user.email}</p>
      </header>

      <main className="grid gap-4 md:grid-cols-2">
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

        <section className="rounded-xl bg-white p-6 shadow">
          <h2 className="mb-3 text-lg font-semibold text-slate-900">Session</h2>
          <p className="mb-2 text-sm text-slate-600">Role: {authState.user.role}</p>
          <p className="mb-4 break-all text-xs text-slate-500">Access token: {authState.accessToken}</p>
          <button
            className="rounded-md bg-slate-700 px-4 py-2 font-medium text-white hover:bg-slate-900 disabled:cursor-not-allowed disabled:opacity-60"
            onClick={handleLogout}
            disabled={loggingOut}
          >
            {loggingOut ? "Logging out..." : "Logout"}
          </button>
        </section>
      </main>

      {error ? <p className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}
    </div>
  );
}