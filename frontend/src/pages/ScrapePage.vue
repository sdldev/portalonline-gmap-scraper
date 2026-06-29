<script setup lang="ts">
import { ref, computed, onMounted } from "vue"
import { useRoute } from "vue-router"
import { useAuthStore } from "@/stores/auth"
import { createJob, listJobs, cancelJob } from "@/services/jobs"
import { useJobStream } from "@/composables/useJobStream"
import ScrapeForm from "@/components/scrape/ScrapeForm.vue"
import ProgressBar from "@/components/scrape/ProgressBar.vue"
import LiveResultsTable from "@/components/scrape/LiveResultsTable.vue"
import BaseButton from "@/components/ui/BaseButton.vue"
import AlertBanner from "@/components/ui/AlertBanner.vue"
import BaseCard from "@/components/ui/BaseCard.vue"
import PageHeader from "@/components/ui/PageHeader.vue"
import TablePagination from "@/components/ui/TablePagination.vue"
import type { JobResponse, JobStatus } from "@/types"

const auth = useAuthStore()
const route = useRoute()

const { leads, collected, total, status, connect } = useJobStream()

const submitting = ref(false)
const error = ref<string | null>(null)
const activeJob = ref<JobResponse | null>(null)
const isRunning = ref(false)
const currentPage = ref(1)
const pageSize = 20

const totalPages = computed(() => Math.max(1, Math.ceil(leads.value.length / pageSize)))

const paginatedLeads = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return leads.value.slice(start, start + pageSize)
})

function handlePageChange(newPage: number) {
  currentPage.value = newPage
}

async function checkActiveJobs() {
  try {
    const page = await listJobs({ status: "running", limit: 1 })
    if (page.jobs.length > 0) {
      const job = page.jobs[0]
      activeJob.value = job
      isRunning.value = true
      status.value = job.status as JobStatus
      collected.value = job.leads_collected
      total.value = job.leads_total
      connect(job.job_id, auth.token!)
      return
    }
    const queuedPage = await listJobs({ status: "queued", limit: 1 })
    if (queuedPage.jobs.length > 0) {
      const job = queuedPage.jobs[0]
      activeJob.value = job
      isRunning.value = true
      status.value = "queued"
      connect(job.job_id, auth.token!)
    }
  } catch {
    // Silent - no active job
  }
}

onMounted(async () => {
  const resumeJobId = route.query.job_id as string | undefined
  if (resumeJobId) {
    connect(resumeJobId, auth.token!)
    isRunning.value = true
    return
  }
  await checkActiveJobs()
})

async function handleSubmit(keyword: string, location: string) {
  submitting.value = true
  error.value = null
  try {
    const job = await createJob({ keyword, location: location || undefined })
    activeJob.value = job
    isRunning.value = true
    connect(job.job_id, auth.token!)
  } catch (e: any) {
    if (e.response?.status === 409) {
      const existingId = e.response.data?.detail?.existing_job_id
      if (existingId) {
        activeJob.value = { job_id: existingId } as JobResponse
        connect(existingId, auth.token!)
        isRunning.value = true
        return
      }
    }
    error.value = e.response?.data?.detail?.message || e.response?.data?.detail || "Failed to start job"
  } finally {
    submitting.value = false
  }
}

async function handleCancel() {
  if (!activeJob.value) return
  try {
    await cancelJob(activeJob.value.job_id)
  } catch {
    // Silent
  }
}
</script>

<template>
  <div class="max-w-4xl">
    <PageHeader title="Scrape" subtitle="Search Google Maps for business leads">
      <template #actions>
        <div v-if="isRunning" class="flex items-center gap-2 px-3 py-1.5 bg-blue-50 border border-blue-200 rounded-full">
          <span class="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
          <span class="text-xs font-medium text-blue-700">{{ status }}</span>
        </div>
      </template>
    </PageHeader>

    <AlertBanner v-if="error" variant="error" :message="error" class="mb-4" />

    <BaseCard padding="p-6" class="mb-6">
      <h3 class="text-sm font-semibold text-gray-900 mb-4">New Search</h3>
      <ScrapeForm :disabled="isRunning" @submit="handleSubmit" />
    </BaseCard>

    <BaseCard v-if="isRunning && activeJob" padding="p-6" class="mb-6">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-sm font-semibold text-gray-900">Progress</h3>
        <BaseButton
          v-if="status === 'queued' || status === 'running'"
          variant="danger"
          size="sm"
          @click="handleCancel"
        >
          Cancel Job
        </BaseButton>
      </div>
      <ProgressBar
        :collected="collected"
        :total="total"
        :status="status"
        :keyword="activeJob.keyword || ''"
        :location="activeJob.location || ''"
      />
    </BaseCard>

    <BaseCard v-if="leads.length > 0" padding="p-6">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-sm font-semibold text-gray-900">Live Results</h3>
        <span class="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-full">{{ leads.length }} leads</span>
      </div>
      <LiveResultsTable :leads="paginatedLeads" />
      <TablePagination
        :current-page="currentPage"
        :total-pages="totalPages"
        @page-change="handlePageChange"
      />
    </BaseCard>
  </div>
</template>
