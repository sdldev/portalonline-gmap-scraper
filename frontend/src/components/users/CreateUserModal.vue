<script setup lang="ts">
import { ref } from "vue"
import BaseModal from "@/components/ui/BaseModal.vue"
import BaseButton from "@/components/ui/BaseButton.vue"
import { createUser } from "@/services/users"

defineProps<{ open: boolean }>()
const emit = defineEmits<{ close: []; created: [] }>()

const username = ref("")
const role = ref("user")
const loading = ref(false)
const error = ref<string | null>(null)
const created = ref<{ username: string; api_key: string } | null>(null)

async function handleCreate() {
  if (!username.value.trim()) return
  loading.value = true
  error.value = null
  try {
    const user = await createUser({ username: username.value.trim(), role: role.value })
    created.value = { username: user.username, api_key: user.api_key }
    emit("created")
  } catch (e: any) {
    error.value = e.response?.data?.detail || "Failed to create user"
  } finally {
    loading.value = false
  }
}

function handleClose() {
  username.value = ""
  role.value = "user"
  error.value = null
  created.value = null
  emit("close")
}

function copyKey() {
  if (created.value) {
    navigator.clipboard.writeText(created.value.api_key)
  }
}
</script>

<template>
  <BaseModal :open="open" title="Add User" @close="handleClose">
    <!-- Result -->
    <div v-if="created" class="space-y-4">
      <div class="p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-800">
        User "{{ created.username }}" created successfully.
      </div>
      <div class="p-4 bg-gray-50 rounded-lg">
        <p class="text-sm text-gray-600 mb-2">API Key (copy now - won't be shown again):</p>
        <div class="flex items-center gap-2">
          <code class="text-xs bg-white px-2 py-1 rounded border flex-1 break-all">{{ created.api_key }}</code>
          <BaseButton variant="secondary" size="sm" @click="copyKey">Copy</BaseButton>
        </div>
      </div>
      <BaseButton variant="ghost" size="sm" @click="handleClose">Close</BaseButton>
    </div>

    <!-- Form -->
    <form v-else @submit.prevent="handleCreate" class="space-y-4">
      <div v-if="error" class="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
        {{ error }}
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Username</label>
        <input
          v-model="username"
          type="text"
          required
          minlength="1"
          maxlength="50"
          class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
          placeholder="only lowercase, numbers, underscore"
        />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Role</label>
        <select
          v-model="role"
          class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
        >
          <option value="user">User</option>
          <option value="admin">Admin</option>
        </select>
      </div>
      <div class="flex justify-end gap-2">
        <BaseButton variant="secondary" @click="handleClose">Cancel</BaseButton>
        <BaseButton variant="primary" type="submit" :loading="loading">Create</BaseButton>
      </div>
    </form>
  </BaseModal>
</template>
