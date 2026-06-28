<script setup lang="ts">
import { ref } from "vue"
import BaseModal from "@/components/ui/BaseModal.vue"
import BaseButton from "@/components/ui/BaseButton.vue"
import { generatePassword } from "@/services/users"
import type { UserResponse } from "@/types"

const props = defineProps<{
  open: boolean
  user: UserResponse | null
}>()

const emit = defineEmits<{ close: [] }>()

const loading = ref(false)
const error = ref<string | null>(null)
const password = ref<string | null>(null)

async function handleGenerate() {
  if (!props.user) return
  loading.value = true
  error.value = null
  try {
    const result = await generatePassword(props.user.user_id)
    password.value = result.password
  } catch (e: any) {
    error.value = e.response?.data?.detail || "Failed to generate password"
  } finally {
    loading.value = false
  }
}

function copyPassword() {
  if (password.value) {
    navigator.clipboard.writeText(password.value)
  }
}

function handleClose() {
  password.value = null
  error.value = null
  emit("close")
}
</script>

<template>
  <BaseModal :open="open" title="Generate Password" @close="handleClose">
    <div class="space-y-4">
      <!-- Confirm step -->
      <div v-if="!password && !loading">
        <p class="text-sm text-gray-600 mb-4">
          Generate a new random password for <strong>{{ user?.username }}</strong>?
        </p>
        <div class="flex justify-end gap-2">
          <BaseButton variant="secondary" @click="handleClose">Cancel</BaseButton>
          <BaseButton variant="primary" @click="handleGenerate">Generate</BaseButton>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="text-center py-4">
        <svg class="animate-spin h-6 w-6 mx-auto text-blue-500" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      </div>

      <!-- Error -->
      <div v-if="error" class="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
        {{ error }}
        <BaseButton variant="secondary" size="sm" class="ml-2" @click="handleClose">Close</BaseButton>
      </div>

      <!-- Result -->
      <div v-if="password" class="space-y-4">
        <div class="p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-800">
          Password generated successfully!
        </div>
        <div class="p-4 bg-gray-50 rounded-lg">
          <p class="text-sm text-gray-600 mb-2">New password (copy now):</p>
          <div class="flex items-center gap-2">
            <code class="text-lg bg-white px-3 py-2 rounded border flex-1 font-mono">{{ password }}</code>
            <BaseButton variant="secondary" size="sm" @click="copyPassword">Copy</BaseButton>
          </div>
        </div>
        <BaseButton variant="ghost" size="sm" @click="handleClose">Close</BaseButton>
      </div>
    </div>
  </BaseModal>
</template>
