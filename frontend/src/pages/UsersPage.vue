<script setup lang="ts">
import { ref, onMounted } from "vue"
import { useRouter } from "vue-router"
import { listUsers, deleteUser as deleteUserApi } from "@/services/users"
import BaseButton from "@/components/ui/BaseButton.vue"
import BaseBadge from "@/components/ui/BaseBadge.vue"
import BaseCard from "@/components/ui/BaseCard.vue"
import ConfirmDialog from "@/components/ui/ConfirmDialog.vue"
import AlertBanner from "@/components/ui/AlertBanner.vue"
import PageHeader from "@/components/ui/PageHeader.vue"
import SkeletonLoader from "@/components/ui/SkeletonLoader.vue"
import GeneratePasswordModal from "@/components/users/GeneratePasswordModal.vue"
import GenerateApiKeyModal from "@/components/users/GenerateApiKeyModal.vue"
import { maskApiKey, relativeDate, copyToClipboard } from "@/utils/formatters"
import { Eye, Pencil, KeyRound, Key, Trash2 } from "lucide-vue-next"
import type { UserResponse } from "@/types"

const router = useRouter()
const users = ref<UserResponse[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

const confirmOpen = ref(false)
const confirmUser = ref<UserResponse | null>(null)
const passwordUser = ref<UserResponse | null>(null)
const passwordModalOpen = ref(false)
const apiKeyUser = ref<UserResponse | null>(null)
const apiKeyModalOpen = ref(false)

async function loadUsers() {
  loading.value = true
  error.value = null
  try {
    users.value = await listUsers()
  } catch (e: any) {
    error.value = e.response?.data?.detail || "Failed to load users"
  } finally {
    loading.value = false
  }
}

onMounted(loadUsers)

async function confirmDeleteUser() {
  if (!confirmUser.value) return
  try {
    await deleteUserApi(confirmUser.value.user_id)
    await loadUsers()
  } catch (e: any) {
    alert(e.response?.data?.detail || "Delete failed")
  } finally {
    confirmOpen.value = false
    confirmUser.value = null
  }
}
</script>

<template>
  <div>
    <PageHeader title="Users">
      <template #actions>
        <BaseButton variant="primary" @click="router.push('/users/new')">+ Add User</BaseButton>
      </template>
    </PageHeader>

    <AlertBanner v-if="error" variant="error" class="mb-4">
      {{ error }}
      <BaseButton variant="secondary" size="sm" class="ml-2" @click="loadUsers">Retry</BaseButton>
    </AlertBanner>

    <BaseCard v-if="loading" padding="p-0">
      <SkeletonLoader :rows="5" height="h-12" />
    </BaseCard>

    <BaseCard v-if="!loading" padding="p-0">
      <div class="overflow-hidden">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Username</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Role</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">API Key</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
              <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-100">
            <tr v-if="users.length === 0">
              <td colspan="6" class="px-4 py-12 text-center text-gray-500">No users found</td>
            </tr>
            <tr v-for="user in users" :key="user.user_id" class="hover:bg-gray-50">
              <td class="px-4 py-3 text-sm font-medium text-gray-900">{{ user.username }}</td>
              <td class="px-4 py-3 text-sm">
                <BaseBadge :variant="user.role === 'admin' ? 'info' : 'default'">{{ user.role }}</BaseBadge>
              </td>
              <td class="px-4 py-3 text-sm">
                <BaseBadge :variant="user.active ? 'success' : 'danger'">{{ user.active ? 'Active' : 'Inactive' }}</BaseBadge>
              </td>
              <td class="px-4 py-3">
                <div class="flex items-center gap-2">
                  <code class="text-xs bg-gray-100 px-1.5 py-0.5 rounded">{{ maskApiKey(user.api_key) }}</code>
                  <button
                    class="text-gray-400 hover:text-gray-600 text-xs"
                    @click="copyToClipboard(user.api_key)"
                    title="Copy API key"
                  >
                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                  </button>
                </div>
              </td>
              <td class="px-4 py-3 text-sm text-gray-500">{{ relativeDate(user.created_at) }}</td>
              <td class="px-4 py-3 text-right">
                <div class="flex gap-1 justify-end">
                  <button
                    class="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                    title="View"
                    @click="router.push(`/users/${user.user_id}`)"
                  >
                    <Eye :size="16" />
                  </button>
                  <button
                    class="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                    title="Edit"
                    @click="router.push(`/users/${user.user_id}/edit`)"
                  >
                    <Pencil :size="16" />
                  </button>
                  <button
                    class="p-1.5 text-gray-400 hover:text-amber-600 hover:bg-amber-50 rounded transition-colors"
                    title="Generate Password"
                    @click="passwordUser = user; passwordModalOpen = true"
                  >
                    <KeyRound :size="16" />
                  </button>
                  <button
                    class="p-1.5 text-gray-400 hover:text-amber-600 hover:bg-amber-50 rounded transition-colors"
                    title="Regenerate API Key"
                    @click="apiKeyUser = user; apiKeyModalOpen = true"
                  >
                    <Key :size="16" />
                  </button>
                  <button
                    class="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                    title="Delete"
                    @click="confirmUser = user; confirmOpen = true"
                  >
                    <Trash2 :size="16" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </BaseCard>

    <ConfirmDialog
      :open="confirmOpen"
      title="Delete User"
      :message="`Delete user \&quot;${confirmUser?.username}\&quot;?`"
      confirm-label="Delete"
      variant="danger"
      @confirm="confirmDeleteUser"
      @cancel="confirmOpen = false; confirmUser = null"
    />

    <GeneratePasswordModal
      :open="passwordModalOpen"
      :user="passwordUser"
      @close="passwordModalOpen = false"
    />
    <GenerateApiKeyModal
      :open="apiKeyModalOpen"
      :user="apiKeyUser"
      @close="apiKeyModalOpen = false"
      @generated="apiKeyModalOpen = false; loadUsers()"
    />
  </div>
</template>
