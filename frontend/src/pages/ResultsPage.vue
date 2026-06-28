<script setup lang="ts">
import { ref, onMounted, watch } from "vue"
import { useRoute, useRouter } from "vue-router"
import { useAuthStore } from "@/stores/auth"
import { listJobs } from "@/services/jobs"
import ResultFilters from "@/components/results/ResultFilters.vue"
import JobsTable from "@/components/results/JobsTable.vue"
import BaseButton from "@/components/ui/BaseButton.vue"
import type { JobResponse, JobsPage } from "@/types"

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const loading = ref(true)
const error = ref<string | null>(null)
const jobs = ref<JobResponse[]>([])
const page = ref(1)
const totalPages = ref(1)
const total = ref(0)

const filters = ref({
  search: "",
  status: "",
  user_id: "",
})

onMounted(async () => {
  // Read from URL query
  filters.value.search = (route.query.keyword as string) || ""
  filters.value.status = (route.query.status as string) || ""
  await loadJobs()
})

async function loadJobs() {
  loading.value = true
  error.value = null
  try {
    const result: JobsPage = await listJobs({
      page: page.value,
      limit: 20,
      keyword: filters.value.search || undefined,
      status: filters.value.status || undefined,
      user_id: filters.value.user_id || undefined,
    })
    jobs.value = result.jobs
    total.value = result.total
    totalPages.value = result.pages
  } catch (e: any) {
    error.value = e.response?.data?.detail || "Failed to load jobs"
  } finally {
    loading.value = false
  }
}

function handleFilter(f: { search: string; status: string; user_id: string }) {
  filters.value = f
  page.value = 1
  // Sync to URL
  router.replace({
    query: {
      ...(f.search && { keyword: f.search }),
      ...(f.status && { status: f.status }),
    },
  })
  loadJobs()
}

function prevPage() {
  if (page.value > 1) {
    page.value--
    loadJobs()
  }
}

function nextPage() {
  if (page.value < totalPages.value) {
    page.value++
    loadJobs()
  }
}
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h2 class="text-xl font-bold text-gray-900">Results</h2>
      <span class="text-sm text-gray-500">{{ total }} job(s)</span>
    </div>

    <ResultFilters @filter="handleFilter" />

    <!-- Error -->
    <div v-if="error" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
      {{ error }}
      <BaseButton variant="secondary" size="sm" class="ml-2" @click="loadJobs">Retry</BaseButton>
    </div>

    <!-- Jobs Table -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-200">
      <JobsTable
        :jobs="jobs"
        :loading="loading"
        :show-user="auth.isAdmin"
        @refresh="loadJobs"
      />
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="flex items-center justify-center gap-4 mt-4">
      <BaseButton variant="secondary" size="sm" :disabled="page <= 1" @click="prevPage">
        Previous
      </BaseButton>
      <span class="text-sm text-gray-500">Page {{ page }} of {{ totalPages }}</span>
      <BaseButton variant="secondary" size="sm" :disabled="page >= totalPages" @click="nextPage">
        Next
      </BaseButton>
    </div>
  </div>
</template>
