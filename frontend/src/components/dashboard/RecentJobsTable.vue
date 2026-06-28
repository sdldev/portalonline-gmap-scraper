<script setup lang="ts">
import { useRouter } from "vue-router"
import BaseTable from "@/components/ui/BaseTable.vue"
import BaseBadge from "@/components/ui/BaseBadge.vue"
import type { RecentJob, JobStatus } from "@/types"

const props = defineProps<{
  jobs: RecentJob[]
  loading: boolean
}>()

const router = useRouter()

const columns = [
  { key: "job_id", header: "Job ID" },
  { key: "keyword", header: "Keyword" },
  { key: "status", header: "Status" },
  { key: "leads", header: "Leads" },
  { key: "created_at", header: "Created" },
]

function statusVariant(status: JobStatus) {
  const map: Record<JobStatus, string> = {
    queued: "warning",
    running: "info",
    completed: "success",
    failed: "danger",
    cancelled: "default",
  }
  return (map[status] || "default") as "default" | "success" | "warning" | "danger" | "info"
}

function formatLeads(job: RecentJob): string {
  return `${job.leads_collected}/${job.leads_total}`
}

function relativeTime(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return "just now"
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

function onRowClick(row: RecentJob) {
  router.push(`/results?keyword=${encodeURIComponent(row.keyword)}`)
}
</script>

<template>
  <BaseTable
    :columns="columns"
    :rows="jobs"
    :loading="loading"
    empty-text="No jobs yet. Start from the Scrape page."
    @row-click="onRowClick"
  >
    <template #cell-job_id="{ value }">
      <code class="text-xs bg-gray-100 px-1.5 py-0.5 rounded">{{ (value as string).slice(0, 8) }}</code>
    </template>
    <template #cell-status="{ value }">
      <BaseBadge :variant="(statusVariant(value as JobStatus) as any)">{{ value }}</BaseBadge>
    </template>
    <template #cell-leads="{ row }">
      {{ formatLeads(row as RecentJob) }}
    </template>
    <template #cell-created_at="{ value }">
      {{ relativeTime(value as string) }}
    </template>
  </BaseTable>
</template>
