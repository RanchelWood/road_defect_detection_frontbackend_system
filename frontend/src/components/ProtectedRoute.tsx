import type { ReactElement } from "react";
import { Navigate } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";

export function ProtectedRoute({ children }: { children: ReactElement }) {
  const { authState } = useAuth();

  if (!authState) {
    return <Navigate to="/login" replace />;
  }

  return children;
}