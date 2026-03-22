import { useState, type ReactNode } from "react";
import { NavLink, useNavigate } from "react-router-dom";

import { logout } from "../api/auth";
import { useAuth } from "../auth/AuthContext";

type AppShellProps = {
  title: string;
  description: string;
  children: ReactNode;
};

function getNavLinkClass(isActive: boolean) {
  return [
    "rounded-md px-3 py-2 text-sm font-medium transition",
    isActive ? "bg-brand-100 text-brand-700" : "text-slate-600 hover:bg-slate-100 hover:text-slate-900",
  ].join(" ");
}

export function AppShell({ title, description, children }: AppShellProps) {
  const navigate = useNavigate();
  const { authState, clearAuth } = useAuth();
  const [loggingOut, setLoggingOut] = useState(false);
  const [logoutError, setLogoutError] = useState<string | null>(null);

  async function handleLogout() {
    if (!authState) {
      return;
    }

    setLoggingOut(true);
    setLogoutError(null);

    try {
      await logout(authState.refreshToken);
    } catch {
      setLogoutError("Logout request failed, but the local session was cleared.");
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
    <div className="min-h-screen">
      <div className="mx-auto flex min-h-screen w-full max-w-6xl flex-col gap-6 p-4 sm:p-6">
        <header className="rounded-2xl bg-white p-5 shadow sm:p-6">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <p className="text-sm font-medium uppercase tracking-[0.2em] text-brand-700">Road Defect System</p>
              <h1 className="mt-2 text-2xl font-semibold text-slate-900">{title}</h1>
              <p className="mt-2 max-w-3xl text-sm text-slate-600">{description}</p>
            </div>

            <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
              <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Signed in</p>
              <p className="mt-1 break-all text-sm font-medium text-slate-900">{authState.user.email}</p>
              <p className="mt-1 text-xs text-slate-500">Role: {authState.user.role}</p>
            </div>
          </div>

          <div className="mt-5 flex flex-col gap-3 border-t border-slate-200 pt-4 sm:flex-row sm:items-center sm:justify-between">
            <nav className="flex flex-wrap gap-2">
              <NavLink className={({ isActive }) => getNavLinkClass(isActive)} to="/dashboard">
                Dashboard
              </NavLink>
              <NavLink className={({ isActive }) => getNavLinkClass(isActive)} to="/inference">
                Inference
              </NavLink>
              <NavLink className={({ isActive }) => getNavLinkClass(isActive)} to="/history">
                History
              </NavLink>
            </nav>

            <button
              className="rounded-md bg-slate-700 px-4 py-2 text-sm font-medium text-white hover:bg-slate-900 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={loggingOut}
              onClick={handleLogout}
              type="button"
            >
              {loggingOut ? "Logging out..." : "Logout"}
            </button>
          </div>

          {logoutError ? (
            <p className="mt-4 rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800">{logoutError}</p>
          ) : null}
        </header>

        <main className="flex-1">{children}</main>
      </div>
    </div>
  );
}
