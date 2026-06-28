import { useToast } from "@/composables/useToast"

export function handleApiError(e: any, fallback = "An error occurred"): string {
  const message = e.response?.data?.detail?.message
    || e.response?.data?.detail
    || e.message
    || fallback

  const toast = useToast()
  toast.add(typeof message === "string" ? message : fallback, "error")
  return typeof message === "string" ? message : fallback
}
