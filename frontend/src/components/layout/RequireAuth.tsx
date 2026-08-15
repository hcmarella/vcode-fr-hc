import { Navigate, Outlet } from "react-router-dom";

import { useCurrentUser } from "../../hooks/useAuth";

export default function RequireAuth() {
  const { data: user, isLoading, isError } = useCurrentUser();

  if (isLoading) {
    return <div className="p-8 text-center text-slate-500">Loading…</div>;
  }

  if (isError || !user) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
}
