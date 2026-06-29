<script setup lang="ts">
import { ref, onMounted } from "vue"
import { useRoute, useRouter } from "vue-router"
import { getJob, getJobResults, cancelJob, deleteJob as deleteJobApi } from "@/services/jobs"
import api from "@/services/api"
import BaseBadge from "@/components/ui/BaseBadge.vue"
import BaseButton from "@/components/ui/BaseButton.vue"
import BaseCard from "@/components/ui/BaseCard.vue"
import BaseTable from "@/components/ui/BaseTable.vue"
import AlertBanner from "@/components/ui/AlertBanner.vue"
import PageHeader from "@/components/ui/PageHeader.vue"
import SkeletonLoader from "@/components/ui/SkeletonLoader.vue"
import ConfirmDialog from "@/components/ui/ConfirmDialog.vue"
import { statusVariant } from "@/utils/formatters"
import type { JobResponse, JobStatus, LeadResponse } from "@/types"

const route = useRoute()
const router = useRouter()
const jobId = route.params.id as string

const job = ref<JobResponse | null>(null)
const jobLoading = ref(true)
const jobError = ref<string | null>(null)

const leads = ref<LeadResponse[]>([])
const leadsLoading = ref(false)
const leadsError = ref<string | null>(null)

const cancelConfirmOpen = ref(false)
const deleteConfirmOpen = ref(false)

const leadColumns = [
  { key: "name", header: "Name" },
  { key: "address", header: "Address" },
  { key: "phone", header: "Phone" },
  { key: "website", header: "Website" },
  { key: "rating", header: "Rating" },
  { key: "review_count", header: "Reviews" },
]

async function loadJob() {
  jobLoading.value = true
  jobError.value = null
  try {
    job.value = await getJob(jobId)
  } catch (e: any) {
    jobError.value = e.response?.data?.detail || "Failed to load job"
  } finally {
    jobLoading.value = false
  }
}

async function loadLeads() {
  leadsLoading.value = true
  leadsError.value = null
  try {
    const result = await getJobResults(jobId)
    leads.value = result.results
  } catch {
    leadsError.value = "Failed to load results"
  } finally {
    leadsLoading.value = false
  }
}

onMounted(async () => {
  await loadJob()
  if (job.value?.status === "completed") {
    await loadLeads()
  }
})

async function exportCsv() {
  try {
    const response = await api.get(`/jobs/${jobId}/results`, {
      params: { format: "csv" },
      responseType: "blob",
    })
    const url = URL.createObjectURL(response.data)
    const a = document.createElement("a")
    a.href = url
    a.download = `job_${jobId.slice(0, 8)}.csv`
    a.click()
    URL.revokeObjectURL(url)
  } catch {
    alert("Failed to download CSV")
  }
}

async function confirmCancel() {
  cancelConfirmOpen.value = false
  try {
    await cancelJob(jobId)
    await loadJob()
  } catch (e: any) {
    alert(e.response?.data?.detail || "Cancel failed")
  }
}

async function confirmDelete() {
  deleteConfirmOpen.value = false
  try {
    await deleteJobApi(jobId)
    router.push("/results")
  } catch (e: any) {
    alert(e.response?.data?.detail || "Delete failed")
  }
}
</script>

<template>
  <div>
    <PageHeader title="Job Details" show-back @back="router.push('/results')">
      <template #actions>
        <code v-if="job" class="text-xs bg-gray-100 px-2 py-1 rounded">{{ job.job_id.slice(0, 8) }}</code>
      </template>
    </PageHeader>

    <BaseCard v-if="jobLoading" padding="p-0">
      <SkeletonLoader :rows="6" height="h-8" />
    </BaseCard>

    <AlertBanner v-else-if="jobError" variant="error" class="mb-4">
      {{ jobError }}
      <BaseButton variant="secondary" size="sm" class="ml-2" @click="loadJob">Retry</BaseButton>
    </AlertBanner>

    <template v-else-if="job">
      <BaseCard>
        <h3 class="text-lg font-semibold text-gray-900 mb-4">Job Information</h3>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
          <div>
            <span class="text-gray-500">Keyword:</span>
            <span class="ml-1 font-medium">{{ job.keyword }}</span>
          </div>
          <div>
            <span class="text-gray-500">Location:</span>
            <span class="ml-1">{{ job.location || "N/A" }}</span>
          </div>
          <div>
            <span class="text-gray-500">Status:</span>
            <BaseBadge :variant="statusVariant(job.status)" class="ml-1">{{ job.status }}</BaseBadge>
          </div>
          <div>
            <span class="text-gray-500">Leads:</span>
            <span class="ml-1">{{ job.leads_collected }}/{{ job.leads_total }}</span>
          </div>
          <div>
            <span class="text-gray-500">Created:</span>
            <span class="ml-1">{{ new Date(job.created_at).toLocaleString() }}</span>
          </div>
          <div v-if="job.completed_at">
            <span class="text-gray-500">Completed:</span>
            <span class="ml-1">{{ new Date(job.completed_at).toLocaleString() }}</span>
          </div>
          <div v-if="job.error" class="sm:col-span-2">
            <span class="text-red-500">Error:</span>
            <span class="ml-1">{{ job.error }}</span>
          </div>
        </div>
        <div class="flex gap-2 mt-6 pt-4 border-t border-gray-200">
          <BaseButton
            v-if="job.status === 'completed'"
            variant="secondary"
            size="sm"
            @click="exportCsv"
          >
            Export CSV
          </BaseButton>
          <BaseButton
            v-if="job.status === 'queued' || job.status === 'running'"
            variant="ghost"
            size="sm"
            @click="router.push('/scrape?job_id=' + job.job_id)"
          >
            View Live
          </BaseButton>
          <BaseButton
            v-if="job.status === 'queued' || job.status === 'running'"
            variant="danger"
            size="sm"
            @click="cancelConfirmOpen = true"
          >
            Cancel
          </BaseButton>
          <BaseButton
            v-if="job.status !== 'queued' && job.status !== 'running'"
            variant="danger"
            size="sm"
            @click="deleteConfirmOpen = true"
          >
            Delete
          </BaseButton>
        </div>
      </BaseCard>

      <div v-if="job.status === 'completed'" class="mt-4">
        <BaseCard>
          <h3 class="text-lg font-semibold text-gray-900 mb-4">Leads</h3>

          <AlertBanner v-if="leadsError" variant="error" :message="leadsError" class="mb-3" />

          <BaseTable
            :columns="leadColumns"
            :rows="leads"
            :loading="leadsLoading"
            empty-text="No leads found"
          >
            <template #cell-name="{ value }">
              <span class="font-medium">{{ value }}</span>
            </template>
            <template #cell-address="{ value }">
              <span class="text-gray-500">{{ value }}</span>
            </template>
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
        </BaseCard>
      </div>
    </template>

    <ConfirmDialog
      :open="cancelConfirmOpen"
      title="Cancel Job"
      message="Cancel this job? The job will stop processing."
      confirm-label="Cancel Job"
      variant="warning"
      @confirm="confirmCancel"
      @cancel="cancelConfirmOpen = false"
    />
    <ConfirmDialog
      :open="deleteConfirmOpen"
      title="Delete Job"
      message="Delete this job and all its leads? This action cannot be undone."
      confirm-label="Delete"
      variant="danger"
      @confirm="confirmDelete"
      @cancel="deleteConfirmOpen = false"
    />
  </div>
</template>
