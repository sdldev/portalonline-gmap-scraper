<script setup lang="ts">
import { ref } from "vue"
import BaseModal from "@/components/ui/BaseModal.vue"
import BaseButton from "@/components/ui/BaseButton.vue"
import AlertBanner from "@/components/ui/AlertBanner.vue"
import SecretDisplay from "@/components/ui/SecretDisplay.vue"
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

function handleClose() {
  password.value = null
  error.value = null
  emit("close")
}
</script>

<template>
  <BaseModal :open="open" title="Generate Password" @close="handleClose">
    <div class="space-y-4">
      <div v-if="!password && !loading">
        <p class="text-sm text-gray-600 mb-4">
          Generate a new random password for <strong>{{ user?.username }}</strong>?
        </p>
        <div class="flex justify-end gap-2">
          <BaseButton variant="secondary" @click="handleClose">Cancel</BaseButton>
          <BaseButton variant="primary" @click="handleGenerate">Generate</BaseButton>
        </div>
      </div>

      <div v-if="loading" class="text-center py-4">
        <svg class="animate-spin h-6 w-6 mx-auto text-blue-500" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" />
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      </div>

      <AlertBanner v-if="error" variant="error">
        {{ error }}
        <BaseButton variant="secondary" size="sm" class="ml-2" @click="handleClose">Close</BaseButton>
      </AlertBanner>

      <div v-if="password" class="space-y-4">
        <AlertBanner variant="success" message="Password generated successfully!" />
        <SecretDisplay label="New password (copy now)" :value="password" monospace />
        <BaseButton variant="ghost" size="sm" @click="handleClose">Close</BaseButton>
      </div>
    </div>
  </BaseModal>
</template>
