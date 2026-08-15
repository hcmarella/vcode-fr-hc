import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { authApi } from "../api/auth";
import { ApiError } from "../api/client";
import type { Team } from "../api/types";

export function useCurrentUser() {
  return useQuery({
    queryKey: ["auth", "me"],
    queryFn: authApi.me,
    retry: false,
    staleTime: 60_000,
    throwOnError: (error) => !(error instanceof ApiError && error.status === 401),
  });
}

export function useLogin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) =>
      authApi.login(email, password),
    onSuccess: (user) => queryClient.setQueryData(["auth", "me"], user),
  });
}

export function useSignup() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      email,
      password,
      name,
      team,
    }: {
      email: string;
      password: string;
      name: string;
      team: Team;
    }) => authApi.signup(email, password, name, team),
    onSuccess: (user) => queryClient.setQueryData(["auth", "me"], user),
  });
}

export function useLogout() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: authApi.logout,
    onSuccess: () => queryClient.setQueryData(["auth", "me"], null),
  });
}
