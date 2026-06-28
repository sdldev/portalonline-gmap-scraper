import axios from "axios"
import { useAuthStore } from "@/stores/auth"
import router from "@/router"

const api = axios.create({
  baseURL: "/api/v1",
  timeout: 30000,
  headers: { "Content-Type": "application/json" },
})

api.interceptors.request.use((config) => {
  const auth = useAuthStore()
  const headers = auth.getAuthHeaders()
  if (headers.Authorization) {
    config.headers.Authorization = headers.Authorization
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const auth = useAuthStore()
      if (auth.isLoggedIn) {
        auth.logout()
        router.push("/login")
      }
    }
    return Promise.reject(error)
  }
)

export default api
