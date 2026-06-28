<script setup lang="ts">
import { ref, onMounted } from "vue"
import { listUsers, deleteUser as deleteUserApi } from "@/services/users"
import BaseButton from "@/components/ui/BaseButton.vue"
import BaseBadge from "@/components/ui/BaseBadge.vue"
import CreateUserModal from "@/components/users/CreateUserModal.vue"
import ViewUserModal from "@/components/users/ViewUserModal.vue"
import EditUserModal from "@/components/users/EditUserModal.vue"
import GeneratePasswordModal from "@/components/users/GeneratePasswordModal.vue"
import GenerateApiKeyModal from "@/components/users/GenerateApiKeyModal.vue"
import type { UserResponse } from "@/types"

const users = ref<UserResponse[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

const createModalOpen = ref(false)
const viewUser = ref<UserResponse | null>(null)
const viewModalOpen = ref(false)
const editUser = ref<UserResponse | null>(null)
const editModalOpen = ref(false)
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

async function handleDelete(user: UserResponse) {
  if (!confirm(`Delete user "${user.username}"?`)) return
  try {
    await deleteUserApi(user.user_id)
    await loadUsers()
  } catch (e: any) {
    alert(e.response?.data?.detail || "Delete failed")
  }
}

function maskApiKey(key: string): string {
  if (!key || key.length < 8) return key
  return key.slice(0, 4) + "****" + key.slice(-4)
}

function copyToClipboard(text: string) {
  navigator.clipboard.writeText(text)
}

function relativeDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString()
}
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h2 class="text-xl font-bold text-gray-900">Users</h2>
      <BaseButton variant="primary" @click="createModalOpen = true">+ Add User</BaseButton>
    </div>

    <!-- Error -->
    <div v-if="error" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
      {{ error }}
      <BaseButton variant="secondary" size="sm" class="ml-2" @click="loadUsers">Retry</BaseButton>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      <div v-for="i in 5" :key="i" class="h-12 bg-gray-200 rounded animate-pulse mb-2" />
    </div>

    <!-- Users Table -->
    <div v-if="!loading" class="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
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
                <BaseButton variant="ghost" size="sm" @click="viewUser = user; viewModalOpen = true">View</BaseButton>
                <BaseButton variant="ghost" size="sm" @click="editUser = user; editModalOpen = true">Edit</BaseButton>
                <BaseButton variant="ghost" size="sm" @click="passwordUser = user; passwordModalOpen = true">Pwd</BaseButton>
                <BaseButton variant="ghost" size="sm" @click="apiKeyUser = user; apiKeyModalOpen = true">Key</BaseButton>
                <BaseButton variant="ghost" size="sm" @click="handleDelete(user)">Del</BaseButton>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Modals -->
    <CreateUserModal
      :open="createModalOpen"
      @close="createModalOpen = false"
      @created="createModalOpen = false; loadUsers()"
    />
    <ViewUserModal
      :open="viewModalOpen"
      :user="viewUser"
      @close="viewModalOpen = false"
    />
    <EditUserModal
      :open="editModalOpen"
      :user="editUser"
      @close="editModalOpen = false"
      @updated="editModalOpen = false; loadUsers()"
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
