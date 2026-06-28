import api from "./api"
import type { DashboardStats, LoginResponse } from "@/types"

export async function login(username: string, password: string): Promise<LoginResponse> {
  const { data } = await api.post("/auth/login", { username, password })
  return data
}

export async function logout(): Promise<void> {
  await api.post("/auth/logout")
}

export async function getStats(): Promise<DashboardStats> {
  const { data } = await api.get("/admin/stats")
  return data
}
