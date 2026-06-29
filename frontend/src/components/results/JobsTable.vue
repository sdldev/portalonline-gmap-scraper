<script setup lang="ts">
import { ref } from "vue"
import { useRouter } from "vue-router"
import BaseTable from "@/components/ui/BaseTable.vue"
import BaseBadge from "@/components/ui/BaseBadge.vue"
import ConfirmDialog from "@/components/ui/ConfirmDialog.vue"
import { cancelJob, deleteJob as deleteJobApi } from "@/services/jobs"
import { statusVariant, relativeTime } from "@/utils/formatters"
import { Eye, FileText, XCircle, Trash2 } from "lucide-vue-next"
import type { JobResponse } from "@/types"

const props = defineProps<{
  jobs: JobResponse[]
  loading: boolean
  showUser: boolean
}>()

const emit = defineEmits<{ refresh: [] }>()

const router = useRouter()
const cancelTarget = ref<JobResponse | null>(null)
const cancelOpen = ref(false)
const deleteTarget = ref<JobResponse | null>(null)
const deleteOpen = ref(false)

const columns = [
  { key: "job_id", header: "Job ID" },
  ...(props.showUser ? [{ key: "username", header: "User" }] : []),
  { key: "keyword", header: "Keyword" },
  { key: "location", header: "Location" },
  { key: "status", header: "Status" },
  { key: "leads", header: "Leads" },
  { key: "created_at", header: "Created" },
  { key: "actions", header: "Actions" },
]

async function confirmCancel() {
  if (!cancelTarget.value) return
  cancelOpen.value = false
  await cancelJob(cancelTarget.value.job_id)
  cancelTarget.value = null
  emit("refresh")
}

async function confirmDelete() {
  if (!deleteTarget.value) return
  deleteOpen.value = false
  await deleteJobApi(deleteTarget.value.job_id)
  deleteTarget.value = null
  emit("refresh")
}

function handleView(job: JobResponse) {
  router.push(`/results/${job.job_id}`)
}
</script>

<template>
  <BaseTable
    :columns="columns"
    :rows="jobs"
    :loading="loading"
    empty-text="No jobs found"
    @row-click="handleView"
  >
    <template #cell-job_id="{ value }">
      <code class="text-xs bg-gray-100 px-1.5 py-0.5 rounded">{{ (value as string).slice(0, 8) }}</code>
    </template>
    <template #cell-status="{ value }">
      <BaseBadge :variant="statusVariant(value as any)">{{ value }}</BaseBadge>
    </template>
    <template #cell-leads="{ row }">
      {{ (row as JobResponse).leads_collected }}/{{ (row as JobResponse).leads_total }}
    </template>
    <template #cell-created_at="{ value }">
      {{ relativeTime(value as string) }}
    </template>
    <template #cell-actions="{ row }">
      <div class="flex gap-1" @click.stop>
        <button
          v-if="(row as JobResponse).status === 'queued' || (row as JobResponse).status === 'running'"
          class="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
          title="View"
          @click="router.push('/scrape?job_id=' + (row as JobResponse).job_id)"
        >
          <Eye :size="16" />
        </button>
        <button
          v-if="(row as JobResponse).status === 'completed' || (row as JobResponse).status === 'failed' || (row as JobResponse).status === 'cancelled'"
          class="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
          title="Details"
          @click="handleView(row as JobResponse)"
        >
          <FileText :size="16" />
        </button>
        <button
          v-if="(row as JobResponse).status === 'queued' || (row as JobResponse).status === 'running'"
          class="p-1.5 text-gray-400 hover:text-amber-600 hover:bg-amber-50 rounded transition-colors"
          title="Cancel"
          @click="cancelTarget = row as JobResponse; cancelOpen = true"
        >
          <XCircle :size="16" />
        </button>
        <button
          v-if="(row as JobResponse).status !== 'queued' && (row as JobResponse).status !== 'running'"
          class="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
          title="Delete"
          @click="deleteTarget = row as JobResponse; deleteOpen = true"
        >
          <Trash2 :size="16" />
        </button>
      </div>
    </template>
  </BaseTable>

  <ConfirmDialog
    :open="cancelOpen"
    title="Cancel Job"
    message="Cancel this job? The job will stop processing."
    confirm-label="Cancel Job"
    variant="warning"
    @confirm="confirmCancel"
    @cancel="cancelOpen = false; cancelTarget = null"
  />
  <ConfirmDialog
    :open="deleteOpen"
    title="Delete Job"
    message="Delete this job and all its leads? This action cannot be undone."
    confirm-label="Delete"
    variant="danger"
    @confirm="confirmDelete"
    @cancel="deleteOpen = false; deleteTarget = null"
  />
</template>
