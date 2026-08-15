import { FormEvent, useState } from "react";
import { Link, Navigate } from "react-router-dom";

import { ApiError } from "../api/client";
import type { Team } from "../api/types";
import { useCurrentUser, useSignup } from "../hooks/useAuth";

const teams: Team[] = ["engineering", "product", "qa", "docs"];

export default function SignupPage() {
  const { data: user } = useCurrentUser();
  const signup = useSignup();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [team, setTeam] = useState<Team>("engineering");

  if (user) return <Navigate to="/" replace />;

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    signup.mutate({ email, password, name, team });
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
          <p className="text-3xl font-semibold leading-tight">Join your team's workspace.</p>
          <p className="mt-3 max-w-sm text-sm text-slate-400">
            Pick your team and you'll only ever see the knowledge base entries scoped to it --
            enforced at the database query level, not just hidden in the UI.
          </p>
        </div>
        <p className="text-xs text-slate-500">vcode-fr-hc</p>
      </div>

      <div className="flex flex-1 flex-col justify-center px-6 py-12 sm:px-12 lg:px-20">
        <div className="mx-auto w-full max-w-sm animate-fade-in-up">
          <h1 className="text-2xl font-semibold text-slate-900">Sign up</h1>
          <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-4">
            <label className="flex flex-col gap-1 text-sm">
              Name
              <input
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="rounded-lg border border-slate-300 px-3 py-2 outline-none focus:border-slate-500"
              />
            </label>
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
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="rounded-lg border border-slate-300 px-3 py-2 outline-none focus:border-slate-500"
              />
            </label>
            <label className="flex flex-col gap-1 text-sm">
              Team
              <select
                value={team}
                onChange={(e) => setTeam(e.target.value as Team)}
                className="rounded-lg border border-slate-300 px-3 py-2 capitalize outline-none focus:border-slate-500"
              >
                {teams.map((t) => (
                  <option key={t} value={t} className="capitalize">
                    {t}
                  </option>
                ))}
              </select>
            </label>
            {signup.isError && (
              <p className="text-sm text-red-600">
                {signup.error instanceof ApiError ? signup.error.message : "Signup failed"}
              </p>
            )}
            <button
              type="submit"
              disabled={signup.isPending}
              className="rounded-lg bg-slate-900 px-3 py-2 text-sm font-medium text-white transition hover:bg-slate-800 disabled:opacity-50"
            >
              {signup.isPending ? "Signing up…" : "Sign up"}
            </button>
          </form>
          <p className="mt-4 text-sm text-slate-500">
            Already have an account?{" "}
            <Link to="/login" className="font-medium text-slate-900 underline">
              Log in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
