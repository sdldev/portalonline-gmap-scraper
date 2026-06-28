import { defineStore } from "pinia"
import { ref, computed } from "vue"
import { login as apiLogin, logout as apiLogout } from "@/services/auth"
import type { LoginResponse } from "@/types"

export const useAuthStore = defineStore("auth", () => {
  const token = ref<string | null>(localStorage.getItem("token"))
  const user = ref<LoginResponse | null>(
    token.value ? JSON.parse(localStorage.getItem("user") || "null") : null
  )

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === "admin")
  const username = computed(() => user.value?.username || "")

  async function login(username: string, password: string) {
    const resp = await apiLogin(username, password)
    token.value = resp.token
    user.value = {
      success: resp.success,
      token: resp.token,
      user_id: resp.user_id,
      username: resp.username,
      role: resp.role,
    }
    localStorage.setItem("token", resp.token)
    localStorage.setItem("user", JSON.stringify(user.value))
    return resp
  }

  async function logout() {
    try {
      await apiLogout()
    } catch {
      // Client-side only
    }
    token.value = null
    user.value = null
    localStorage.removeItem("token")
    localStorage.removeItem("user")
  }

  function getAuthHeaders(): Record<string, string> {
    if (!token.value) return {}
    return { Authorization: `Bearer ${token.value}` }
  }

  return { token, user, isLoggedIn, isAdmin, username, login, logout, getAuthHeaders }
})
