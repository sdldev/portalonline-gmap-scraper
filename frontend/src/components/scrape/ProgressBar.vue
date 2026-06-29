<script setup lang="ts">
import { computed } from "vue"
import { Loader2, CheckCircle2, XCircle, Clock, Ban } from "lucide-vue-next"
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
  if (props.status === "cancelled") return "bg-gray-400"
  return "bg-blue-500"
})

const statusConfig = computed(() => {
  switch (props.status) {
    case "queued":
      return { icon: Clock, text: "Waiting in queue...", color: "text-amber-600", bg: "bg-amber-50", border: "border-amber-200" }
    case "running":
      return { icon: Loader2, text: `Scraping: ${props.keyword}${props.location ? " in " + props.location : ""}`, color: "text-blue-600", bg: "bg-blue-50", border: "border-blue-200" }
    case "completed":
      return { icon: CheckCircle2, text: `Completed! ${props.collected} leads found.`, color: "text-green-600", bg: "bg-green-50", border: "border-green-200" }
    case "failed":
      return { icon: XCircle, text: "Failed: check job details", color: "text-red-600", bg: "bg-red-50", border: "border-red-200" }
    case "cancelled":
      return { icon: Ban, text: "Cancelled", color: "text-gray-600", bg: "bg-gray-50", border: "border-gray-200" }
    default:
      return { icon: Clock, text: "", color: "text-gray-600", bg: "bg-gray-50", border: "border-gray-200" }
  }
})
</script>

<template>
  <div class="space-y-3">
    <!-- Status banner -->
    <div :class="['flex items-center gap-3 px-4 py-3 rounded-lg border', statusConfig.bg, statusConfig.border]">
      <component
        :is="statusConfig.icon"
        :size="20"
        :stroke-width="1.5"
        :class="[statusConfig.color, status === 'running' ? 'animate-spin' : '']"
      />
      <span :class="['text-sm font-medium', statusConfig.color]">{{ statusConfig.text }}</span>
    </div>

    <!-- Progress bar -->
    <div class="space-y-1">
      <div class="flex justify-between text-xs text-gray-500">
        <span>{{ collected }} of {{ total }} leads</span>
        <span>{{ percentage }}%</span>
      </div>
      <div class="h-2.5 bg-gray-200 rounded-full overflow-hidden">
        <div
          :class="['h-full rounded-full transition-all duration-500', barColor]"
          :style="{ width: percentage + '%' }"
        />
      </div>
    </div>

    <!-- Stats -->
    <div class="flex gap-4 text-center">
      <div class="flex-1 px-3 py-2 bg-gray-50 rounded-lg">
        <p class="text-lg font-bold text-gray-900">{{ collected }}</p>
        <p class="text-xs text-gray-500">Collected</p>
      </div>
      <div class="flex-1 px-3 py-2 bg-gray-50 rounded-lg">
        <p class="text-lg font-bold text-gray-900">{{ total }}</p>
        <p class="text-xs text-gray-500">Target</p>
      </div>
      <div class="flex-1 px-3 py-2 bg-gray-50 rounded-lg">
        <p class="text-lg font-bold" :class="status === 'completed' ? 'text-green-600' : 'text-gray-900'">{{ percentage }}%</p>
        <p class="text-xs text-gray-500">Progress</p>
      </div>
    </div>
  </div>
</template>
