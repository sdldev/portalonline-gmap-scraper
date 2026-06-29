<script setup lang="ts">
import { useRouter } from "vue-router"
import BaseTable from "@/components/ui/BaseTable.vue"
import BaseBadge from "@/components/ui/BaseBadge.vue"
import { statusVariant, relativeTime } from "@/utils/formatters"
import type { RecentJob } from "@/types"

defineProps<{
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
      <BaseBadge :variant="statusVariant(value as any)">{{ value }}</BaseBadge>
    </template>
    <template #cell-leads="{ row }">
      {{ (row as RecentJob).leads_collected }}/{{ (row as RecentJob).leads_total }}
    </template>
    <template #cell-created_at="{ value }">
      {{ relativeTime(value as string) }}
    </template>
  </BaseTable>
</template>
