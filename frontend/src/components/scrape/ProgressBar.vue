<script setup lang="ts">
import { computed } from "vue"
import type { JobStatus } from "@/types"

const props = defineProps<{
  collected: number
  total: number
  status: JobStatus
  keyword: string
  location: string
}>()

const percentage = computed(() => {
  if (props.total === 0) return 0
  return Math.min(100, Math.round((props.collected / props.total) * 100))
})

const barColor = computed(() => {
  if (props.status === "completed") return "bg-green-500"
  if (props.status === "failed") return "bg-red-500"
  return "bg-blue-500"
})

const statusText = computed(() => {
  switch (props.status) {
    case "queued":
      return "Waiting in queue..."
    case "running":
      return `Scraping: ${props.keyword}${props.location ? " in " + props.location : ""}...`
    case "completed":
      return `Completed! ${props.collected} leads found.`
    case "failed":
      return "Failed: check job details"
    case "cancelled":
      return "Cancelled"
    default:
      return ""
  }
})
</script>

<template>
  <div class="space-y-2">
    <div class="flex justify-between text-sm">
      <span>{{ statusText }}</span>
      <span class="text-gray-500">{{ collected }}/{{ total }} ({{ percentage }}%)</span>
    </div>
    <div class="h-3 bg-gray-200 rounded-full overflow-hidden">
      <div
        :class="['h-full rounded-full transition-all duration-500', barColor]"
        :style="{ width: percentage + '%' }"
      />
    </div>
  </div>
</template>
