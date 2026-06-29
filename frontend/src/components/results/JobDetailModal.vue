<script setup lang="ts">
import { ref, watch } from "vue"
import BaseModal from "@/components/ui/BaseModal.vue"
import BaseBadge from "@/components/ui/BaseBadge.vue"
import BaseButton from "@/components/ui/BaseButton.vue"
import BaseTable from "@/components/ui/BaseTable.vue"
import { getJobResults } from "@/services/jobs"
import { statusVariant } from "@/utils/formatters"
import type { JobResponse, LeadResponse } from "@/types"

const props = defineProps<{
  open: boolean
  job: JobResponse | null
}>()

const emit = defineEmits<{ close: [] }>()

const loading = ref(false)
const error = ref<string | null>(null)
const leads = ref<LeadResponse[]>([])

const leadColumns = [
  { key: "name", header: "Name" },
  { key: "address", header: "Address" },
  { key: "phone", header: "Phone" },
  { key: "website", header: "Website" },
]

watch(
  () => [props.open, props.job],
  async ([open, job]) => {
    if (!open || !job || typeof job !== "object") return
    loading.value = true
    error.value = null
    leads.value = []
    try {
      const result = await getJobResults(job.job_id)
      leads.value = result.results
    } catch {
      error.value = "Failed to load results"
    } finally {
      loading.value = false
    }
  }
)

function exportCsv() {
  if (!props.job) return
  window.open(`/api/v1/jobs/${props.job.job_id}/results?format=csv`)
}
</script>

<template>
  <BaseModal :open="open" :title="job ? 'Job: ' + job.job_id.slice(0, 8) : 'Job Details'" size="lg" @close="emit('close')">
    <div v-if="job" class="space-y-4">
      <div class="grid grid-cols-2 gap-3 text-sm">
        <div><span class="text-gray-500">Keyword:</span> {{ job.keyword }}</div>
        <div><span class="text-gray-500">Location:</span> {{ job.location || "N/A" }}</div>
        <div>
          <span class="text-gray-500">Status:</span>
          <BaseBadge :variant="statusVariant(job.status)">{{ job.status }}</BaseBadge>
        </div>
        <div><span class="text-gray-500">Leads:</span> {{ job.leads_collected }}/{{ job.leads_total }}</div>
        <div><span class="text-gray-500">Created:</span> {{ new Date(job.created_at).toLocaleString() }}</div>
        <div v-if="job.error"><span class="text-red-500">Error:</span> {{ job.error }}</div>
      </div>

      <div v-if="error" class="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
        {{ error }}
      </div>

      <div>
        <p class="text-sm text-gray-500 mb-2">{{ leads.length }} lead(s)</p>
        <BaseTable
          :columns="leadColumns"
          :rows="leads"
          :loading="loading"
          empty-text="No leads found"
        >
          <template #cell-website="{ value }">
            <a
              v-if="value && value !== 'N/A'"
              :href="value as string"
              target="_blank"
              class="text-blue-600 hover:underline"
            >
              {{ (value as string).slice(0, 30) }}
            </a>
            <span v-else class="text-gray-400">N/A</span>
          </template>
        </BaseTable>
      </div>

      <div class="flex justify-end gap-2 pt-4 border-t border-gray-200">
        <BaseButton variant="secondary" size="sm" @click="exportCsv">Export CSV</BaseButton>
        <BaseButton variant="ghost" size="sm" @click="emit('close')">Close</BaseButton>
      </div>
    </div>
  </BaseModal>
</template>
