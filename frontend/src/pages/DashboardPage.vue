<script setup lang="ts">
import { ref, onMounted, computed } from "vue"
import { useAuthStore } from "@/stores/auth"
import { getStats } from "@/services/auth"
import { listJobs } from "@/services/jobs"
import StatCard from "@/components/dashboard/StatCard.vue"
import RecentJobsTable from "@/components/dashboard/RecentJobsTable.vue"
import BaseButton from "@/components/ui/BaseButton.vue"
import type { DashboardStats, RecentJob } from "@/types"

const auth = useAuthStore()
const loading = ref(true)
const error = ref<string | null>(null)
const stats = ref<DashboardStats | null>(null)

onMounted(async () => {
  try {
    if (auth.isAdmin) {
      stats.value = await getStats()
    } else {
      const jobsPage = await listJobs({ limit: 10 })
      stats.value = {
        total_users: 0,
        total_jobs: jobsPage.total,
        total_leads: 0,
        active_jobs: jobsPage.jobs.filter(j => j.status === "running").length,
        queued_jobs: jobsPage.jobs.filter(j => j.status === "queued").length,
        recent_jobs: jobsPage.jobs.slice(0, 10).map(j => ({
          job_id: j.job_id,
          keyword: j.keyword,
          location: j.location,
          status: j.status,
          leads_collected: j.leads_collected,
          leads_total: j.leads_total,
          created_at: j.created_at,
        })) as RecentJob[],
      }
    }
  } catch (e: any) {
    error.value = e.response?.data?.detail || "Failed to load dashboard"
  } finally {
    loading.value = false
  }
})

async function retry() {
  error.value = null
  loading.value = true
  // trigger onMounted again by reloading
  window.location.reload()
}
</script>

<template>
  <div>
    <h2 class="text-xl font-bold text-gray-900 mb-6">Dashboard</h2>

    <!-- Error -->
    <div
      v-if="error"
      class="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center justify-between"
    >
      <span class="text-sm text-red-700">{{ error }}</span>
      <BaseButton variant="secondary" size="sm" @click="retry">Retry</BaseButton>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
      <div v-for="i in 3" :key="i" class="bg-white rounded-xl shadow-sm border border-gray-200 p-6 animate-pulse">
        <div class="h-4 bg-gray-200 rounded w-1/3 mb-2" />
        <div class="h-8 bg-gray-200 rounded w-1/2" />
      </div>
    </div>

    <!-- Stats -->
    <div v-if="stats && !loading" class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
      <StatCard
        v-if="auth.isAdmin"
        label="Total Users"
        :value="stats.total_users"
      />
      <StatCard
        label="Total Jobs"
        :value="stats.total_jobs"
      />
      <StatCard
        label="Total Leads"
        :value="stats.total_leads"
      />
    </div>

    <!-- Active/queued indicators -->
    <div v-if="stats && !loading" class="flex gap-4 mb-6">
      <div class="bg-blue-50 text-blue-700 px-4 py-2 rounded-lg text-sm font-medium">
        Active: {{ stats.active_jobs }}
      </div>
      <div class="bg-amber-50 text-amber-700 px-4 py-2 rounded-lg text-sm font-medium">
        Queued: {{ stats.queued_jobs }}
      </div>
    </div>

    <!-- Recent Jobs -->
    <div v-if="stats && !loading" class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <h3 class="text-lg font-semibold text-gray-900 mb-4">Recent Jobs</h3>
      <RecentJobsTable :jobs="stats.recent_jobs" :loading="false" />
    </div>
  </div>
</template>
