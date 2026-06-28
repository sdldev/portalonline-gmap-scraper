<script setup lang="ts">
import { ref, watch } from "vue"
import BaseModal from "@/components/ui/BaseModal.vue"
import BaseButton from "@/components/ui/BaseButton.vue"
import { updateUser } from "@/services/users"
import type { UserResponse } from "@/types"

const props = defineProps<{
  open: boolean
  user: UserResponse | null
}>()

const emit = defineEmits<{ close: []; updated: [] }>()

const username = ref("")
const role = ref("user")
const active = ref(true)
const loading = ref(false)
const error = ref<string | null>(null)

watch(
  () => [props.open, props.user],
  ([open, user]) => {
    if (!open || !user || typeof user !== "object") return
    username.value = user.username
    role.value = user.role
    active.value = user.active
  }
)

async function handleUpdate() {
  if (!props.user) return
  loading.value = true
  error.value = null
  try {
    await updateUser(props.user.user_id, {
      username: username.value.trim() || undefined,
      role: role.value,
      active: active.value,
    })
    emit("updated")
  } catch (e: any) {
    error.value = e.response?.data?.detail || "Failed to update user"
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <BaseModal :open="open" title="Edit User" @close="emit('close')">
    <form v-if="user" @submit.prevent="handleUpdate" class="space-y-4">
      <div v-if="error" class="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
        {{ error }}
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1">Username</label>
        <input
          v-model="username"
          type="text"
          required
          class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
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
      <div class="flex items-center gap-2">
        <input id="active-toggle" v-model="active" type="checkbox" class="rounded" />
        <label for="active-toggle" class="text-sm text-gray-700">Active</label>
      </div>
      <div class="flex justify-end gap-2">
        <BaseButton variant="secondary" @click="emit('close')">Cancel</BaseButton>
        <BaseButton variant="primary" type="submit" :loading="loading">Save</BaseButton>
      </div>
    </form>
  </BaseModal>
</template>
