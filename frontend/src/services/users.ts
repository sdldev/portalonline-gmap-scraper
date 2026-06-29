import api from "./api"
import type { UserCreatePayload, UserResponse, UserUpdatePayload } from "@/types"

export async function listUsers(): Promise<UserResponse[]> {
  const { data } = await api.get("/users")
  return data
}

export async function getUser(userId: string): Promise<UserResponse> {
  const { data } = await api.get(`/users/${userId}`)
  return data
}

export async function createUser(payload: UserCreatePayload): Promise<UserResponse> {
  const { data } = await api.post("/users", payload)
  return data
}

export async function updateUser(
  userId: string,
  payload: UserUpdatePayload
): Promise<UserResponse> {
  const { data } = await api.patch(`/users/${userId}`, payload)
  return data
}

export async function deleteUser(userId: string): Promise<void> {
  await api.delete(`/users/${userId}`)
}

export async function updatePassword(userId: string, password: string): Promise<{ success: boolean }> {
  const { data } = await api.put(`/users/${userId}/update-password`, { password })
  return data
}

export async function generatePassword(userId: string): Promise<{ success: boolean; password: string }> {
  const { data } = await api.post(`/users/${userId}/generate-password`)
  return data
}

export async function generateApiKey(userId: string): Promise<{ success: boolean; api_key: string }> {
  const { data } = await api.post(`/users/${userId}/generate-api-key`)
  return data
}
