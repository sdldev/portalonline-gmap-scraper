<script setup lang="ts">
import { ref, onMounted } from "vue"
import { useRoute, useRouter } from "vue-router"
import { useAuthStore } from "@/stores/auth"
import { listJobs } from "@/services/jobs"
import ResultFilters from "@/components/results/ResultFilters.vue"
import JobsTable from "@/components/results/JobsTable.vue"
import BaseButton from "@/components/ui/BaseButton.vue"
import BaseCard from "@/components/ui/BaseCard.vue"
import AlertBanner from "@/components/ui/AlertBanner.vue"
import PageHeader from "@/components/ui/PageHeader.vue"
import TablePagination from "@/components/ui/TablePagination.vue"
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
  router.replace({
    query: {
      ...(f.search && { keyword: f.search }),
      ...(f.status && { status: f.status }),
    },
  })
  loadJobs()
}

function handlePageChange(newPage: number) {
  page.value = newPage
  loadJobs()
}
</script>

<template>
  <div>
    <PageHeader title="Results">
      <template #actions>
        <span class="text-sm text-gray-500">{{ total }} job(s)</span>
      </template>
    </PageHeader>

    <ResultFilters @filter="handleFilter" />

    <AlertBanner v-if="error" variant="error" class="mb-4">
      {{ error }}
      <BaseButton variant="secondary" size="sm" class="ml-2" @click="loadJobs">Retry</BaseButton>
    </AlertBanner>

    <BaseCard padding="p-0">
      <JobsTable
        :jobs="jobs"
        :loading="loading"
        :show-user="auth.isAdmin"
        @refresh="loadJobs"
      />
    </BaseCard>

    <TablePagination
      :current-page="page"
      :total-pages="totalPages"
      @page-change="handlePageChange"
    />
  </div>
</template>
