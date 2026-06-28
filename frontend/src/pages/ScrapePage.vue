<script setup lang="ts">
import { ref, onMounted } from "vue"
import { useRoute } from "vue-router"
import { useAuthStore } from "@/stores/auth"
import { createJob, listJobs, cancelJob } from "@/services/jobs"
import { useJobStream } from "@/composables/useJobStream"
import ScrapeForm from "@/components/scrape/ScrapeForm.vue"
import ProgressBar from "@/components/scrape/ProgressBar.vue"
import LiveResultsTable from "@/components/scrape/LiveResultsTable.vue"
import BaseButton from "@/components/ui/BaseButton.vue"
import type { JobResponse, JobStatus } from "@/types"

const auth = useAuthStore()
const route = useRoute()

const { leads, collected, total, status, connect } = useJobStream()

const submitting = ref(false)
const error = ref<string | null>(null)
const activeJob = ref<JobResponse | null>(null)
const isRunning = ref(false)

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
  <div>
    <h2 class="text-xl font-bold text-gray-900 mb-6">Scrape</h2>

    <!-- Error -->
    <div v-if="error" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
      {{ error }}
    </div>

    <!-- Form -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
      <ScrapeForm :disabled="isRunning" @submit="handleSubmit" />
    </div>

    <!-- Progress -->
    <div v-if="isRunning && activeJob" class="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
      <ProgressBar
        :collected="collected"
        :total="total"
        :status="status"
        :keyword="activeJob.keyword || ''"
        :location="activeJob.location || ''"
      />
      <div class="mt-4 flex justify-end">
        <BaseButton
          v-if="status === 'queued' || status === 'running'"
          variant="danger"
          size="sm"
          @click="handleCancel"
        >
          Cancel
        </BaseButton>
      </div>
    </div>

    <!-- Live Results -->
    <div v-if="leads.length > 0" class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h3 class="text-lg font-semibold text-gray-900 mb-4">Live Results ({{ leads.length }})</h3>
      <LiveResultsTable :leads="leads" />
    </div>
  </div>
</template>
