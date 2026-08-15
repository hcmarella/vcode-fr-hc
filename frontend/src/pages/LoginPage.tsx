import { FormEvent, useState } from "react";
import { Link, Navigate } from "react-router-dom";

import { ApiError } from "../api/client";
import { useCurrentUser, useLogin } from "../hooks/useAuth";

export default function LoginPage() {
  const { data: user } = useCurrentUser();
  const login = useLogin();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  if (user) return <Navigate to="/" replace />;

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    login.mutate({ email, password });
  }

  return (
    <div className="flex min-h-screen">
      <div className="hidden flex-1 flex-col justify-between bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-10 text-white lg:flex">
        <span className="flex items-center gap-2 text-lg font-semibold">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-white/10 text-sm font-bold">
            P
          </span>
          portal
        </span>
        <div className="animate-fade-in-up">
          <p className="text-3xl font-semibold leading-tight">
            Personas, skills, and knowledge, always in sync.
          </p>
          <p className="mt-3 max-w-sm text-sm text-slate-400">
            Pulled live from vcode-w-hc on every push. Ask about any of it, or trigger real Jira
            actions, right from the chat widget.
          </p>
        </div>
        <p className="text-xs text-slate-500">vcode-fr-hc</p>
      </div>

      <div className="flex flex-1 flex-col justify-center px-6 py-12 sm:px-12 lg:px-20">
        <div className="mx-auto w-full max-w-sm animate-fade-in-up">
          <h1 className="text-2xl font-semibold text-slate-900">Log in</h1>
          <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-4">
            <label className="flex flex-col gap-1 text-sm">
              Email
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="rounded-lg border border-slate-300 px-3 py-2 outline-none focus:border-slate-500"
              />
            </label>
            <label className="flex flex-col gap-1 text-sm">
              Password
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="rounded-lg border border-slate-300 px-3 py-2 outline-none focus:border-slate-500"
              />
            </label>
            {login.isError && (
              <p className="text-sm text-red-600">
                {login.error instanceof ApiError ? login.error.message : "Login failed"}
              </p>
            )}
            <button
              type="submit"
              disabled={login.isPending}
              className="rounded-lg bg-slate-900 px-3 py-2 text-sm font-medium text-white transition hover:bg-slate-800 disabled:opacity-50"
            >
              {login.isPending ? "Logging in…" : "Log in"}
            </button>
          </form>
          <p className="mt-4 text-sm text-slate-500">
            No account?{" "}
            <Link to="/signup" className="font-medium text-slate-900 underline">
              Sign up
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
