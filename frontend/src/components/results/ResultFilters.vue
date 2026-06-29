<script setup lang="ts">
import { ref, watch, computed } from "vue"
import { useAuthStore } from "@/stores/auth"
import { listUsers } from "@/services/users"
import BaseInput from "@/components/ui/BaseInput.vue"
import BaseSelect from "@/components/ui/BaseSelect.vue"
import type { UserResponse } from "@/types"

const emit = defineEmits<{
  filter: [filters: { search: string; status: string; user_id: string }]
}>()

const auth = useAuthStore()
const search = ref("")
const status = ref("")
const userId = ref("")
const users = ref<UserResponse[]>([])

let debounceTimer: ReturnType<typeof setTimeout> | null = null

function emitFilters() {
  emit("filter", {
    search: search.value,
    status: status.value,
    user_id: userId.value,
  })
}

watch(search, () => {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(emitFilters, 300)
})

watch([status, userId], emitFilters)

async function loadUsers() {
  if (!auth.isAdmin) return
  try {
    users.value = await listUsers()
  } catch {
    // Silent
  }
}

loadUsers()

const statusOptions = [
  { value: "", label: "All Status" },
  { value: "queued", label: "Queued" },
  { value: "running", label: "Running" },
  { value: "completed", label: "Completed" },
  { value: "failed", label: "Failed" },
  { value: "cancelled", label: "Cancelled" },
]

const userOptions = computed(() => [
  { value: "", label: "All Users" },
  ...users.value.map(u => ({ value: u.user_id, label: u.username })),
])
</script>

<template>
  <div class="flex flex-wrap gap-3 mb-4">
    <BaseInput
      v-model="search"
      id="filter-search"
      name="search"
      placeholder="Search keyword..."
      class="w-48"
    />
    <BaseSelect
      v-model="status"
      id="filter-status"
      name="status"
      :options="statusOptions"
    />
    <BaseSelect
      v-if="auth.isAdmin"
      v-model="userId"
      id="filter-user"
      name="user_id"
      :options="userOptions"
    />
  </div>
</template>
