<script setup lang="ts">
import { ref, onMounted } from "vue"
import { useAuthStore } from "@/stores/auth"
import { getStatsCounts } from "@/services/auth"
import { listJobs } from "@/services/jobs"
import StatCard from "@/components/dashboard/StatCard.vue"
import RecentJobsTable from "@/components/dashboard/RecentJobsTable.vue"
import BaseButton from "@/components/ui/BaseButton.vue"
import BaseCard from "@/components/ui/BaseCard.vue"
import AlertBanner from "@/components/ui/AlertBanner.vue"
import PageHeader from "@/components/ui/PageHeader.vue"
import SkeletonLoader from "@/components/ui/SkeletonLoader.vue"
import EmptyState from "@/components/ui/EmptyState.vue"
import TablePagination from "@/components/ui/TablePagination.vue"
import type { RecentJob, StatsCounts } from "@/types"

const auth = useAuthStore()
const loading = ref(true)
const error = ref<string | null>(null)
const counts = ref<StatsCounts>({
  total_users: 0,
  total_jobs: 0,
  total_leads: 0,
  active_jobs: 0,
  queued_jobs: 0,
})
const recentJobs = ref<RecentJob[]>([])
const page = ref(1)
const totalPages = ref(1)

async function loadDashboard(p = 1) {
  loading.value = true
  error.value = null
  try {
    if (auth.isAdmin) {
      const [countsResult, jobsResult] = await Promise.all([
        getStatsCounts(),
        listJobs({ page: p, limit: 10 }),
      ])
      counts.value = countsResult
      recentJobs.value = jobsResult.jobs.map(j => ({
        job_id: j.job_id,
        keyword: j.keyword,
        location: j.location,
        status: j.status,
        leads_collected: j.leads_collected,
        leads_total: j.leads_total,
        created_at: j.created_at,
      })) as RecentJob[]
      totalPages.value = jobsResult.pages
    } else {
      const jobsResult = await listJobs({ page: p, limit: 10 })
      counts.value = {
        total_users: 0,
        total_jobs: jobsResult.total,
        total_leads: 0,
        active_jobs: 0,
        queued_jobs: 0,
      }
      recentJobs.value = jobsResult.jobs.map(j => ({
        job_id: j.job_id,
        keyword: j.keyword,
        location: j.location,
        status: j.status,
        leads_collected: j.leads_collected,
        leads_total: j.leads_total,
        created_at: j.created_at,
      })) as RecentJob[]
      totalPages.value = jobsResult.pages
    }
    page.value = p
  } catch (e: any) {
    error.value = e.response?.data?.detail || "Failed to load dashboard"
  } finally {
    loading.value = false
  }
}

function handlePageChange(newPage: number) {
  loadDashboard(newPage)
}

onMounted(() => loadDashboard())
</script>

<template>
  <div>
    <PageHeader title="Dashboard" subtitle="Overview of your scraping activity" />

    <AlertBanner v-if="error" variant="error" class="mb-4">
      {{ error }}
      <BaseButton variant="secondary" size="sm" class="ml-2" @click="loadDashboard()">Retry</BaseButton>
    </AlertBanner>

    <template v-if="loading && !error">
      <BaseCard padding="p-0">
        <SkeletonLoader :rows="5" height="h-20" />
      </BaseCard>
    </template>

    <template v-else-if="counts">
      <!-- Stat Cards -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <StatCard label="Total Jobs" :value="counts.total_jobs" />
        <StatCard label="Total Leads" :value="counts.total_leads" />
        <StatCard label="Active Jobs" :value="counts.active_jobs" />
        <StatCard label="Queued Jobs" :value="counts.queued_jobs" />
        <StatCard v-if="auth.isAdmin" label="Total Users" :value="counts.total_users" />
      </div>

      <!-- Recent Jobs -->
      <BaseCard>
        <h3 class="text-lg font-semibold text-gray-900 mb-4">Recent Jobs</h3>
        <RecentJobsTable
          v-if="recentJobs.length > 0"
          :jobs="recentJobs"
          :loading="false"
        />
        <EmptyState
          v-else
          title="No jobs yet"
          description="Start scraping from the Scrape page to see results here."
        />
        <TablePagination
          :current-page="page"
          :total-pages="totalPages"
          @page-change="handlePageChange"
        />
      </BaseCard>
    </template>
  </div>
</template>
