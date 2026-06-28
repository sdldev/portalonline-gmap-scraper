import { ref, onUnmounted } from "vue"
import type { SSEProgress, LeadResponse, JobStatus } from "@/types"
import { getJobStreamUrl } from "@/services/jobs"

export function useJobStream() {
  const leads = ref<LeadResponse[]>([])
  const collected = ref(0)
  const total = ref(0)
  const status = ref<JobStatus>("queued")
  const connected = ref(false)
  const error = ref<string | null>(null)

  let eventSource: EventSource | null = null
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  let reconnectAttempts = 0

  function connect(jobId: string, token: string) {
    close()
    const url = getJobStreamUrl(token, jobId)
    eventSource = new EventSource(url)
    eventSource.onopen = () => {
      connected.value = true
      reconnectAttempts = 0
    }
    eventSource.onmessage = (event) => {
      const data: SSEProgress = JSON.parse(event.data)
      switch (data.event) {
        case "progress":
          if (data.leads_collected != null) collected.value = data.leads_collected
          if (data.total_leads != null) total.value = data.total_leads
          if (data.lead) leads.value.unshift(data.lead)
          break
        case "status_change":
          if (data.new) status.value = data.new
          break
        case "completed":
          if (data.status) status.value = data.status
          close()
          break
      }
    }
    eventSource.onerror = () => {
      connected.value = false
      close()
      const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 16000)
      reconnectAttempts++
      reconnectTimer = setTimeout(() => connect(jobId, token), delay)
    }
  }

  function close() {
    eventSource?.close()
    eventSource = null
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
  }

  onUnmounted(close)

  return { leads, collected, total, status, connected, error, connect, close }
}
