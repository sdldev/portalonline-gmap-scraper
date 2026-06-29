<script setup lang="ts">
import { ref } from "vue"
import BaseModal from "@/components/ui/BaseModal.vue"
import BaseButton from "@/components/ui/BaseButton.vue"
import AlertBanner from "@/components/ui/AlertBanner.vue"
import SecretDisplay from "@/components/ui/SecretDisplay.vue"
import { generateApiKey } from "@/services/users"
import type { UserResponse } from "@/types"

const props = defineProps<{
  open: boolean
  user: UserResponse | null
}>()

const emit = defineEmits<{ close: []; generated: [] }>()

const loading = ref(false)
const error = ref<string | null>(null)
const apiKey = ref<string | null>(null)

async function handleRegenerate() {
  if (!props.user) return
  loading.value = true
  error.value = null
  try {
    const result = await generateApiKey(props.user.user_id)
    apiKey.value = result.api_key
    emit("generated")
  } catch (e: any) {
    error.value = e.response?.data?.detail || "Failed to regenerate API key"
  } finally {
    loading.value = false
  }
}

function handleClose() {
  apiKey.value = null
  error.value = null
  emit("close")
}
</script>

<template>
  <BaseModal :open="open" title="Regenerate API Key" @close="handleClose">
    <div class="space-y-4">
      <div v-if="!apiKey && !loading">
        <AlertBanner variant="warning" class="mb-4">
          The old API key for <strong>{{ user?.username }}</strong> will be immediately invalidated.
          All services using the old key will stop working.
        </AlertBanner>
        <div class="flex justify-end gap-2">
          <BaseButton variant="secondary" @click="handleClose">Cancel</BaseButton>
          <BaseButton variant="danger" @click="handleRegenerate">Regenerate</BaseButton>
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

      <div v-if="apiKey" class="space-y-4">
        <AlertBanner variant="success" message="API key regenerated! The old key is no longer valid." />
        <SecretDisplay label="New API key (copy now)" :value="apiKey" />
        <BaseButton variant="ghost" size="sm" @click="handleClose">Close</BaseButton>
      </div>
    </div>
  </BaseModal>
</template>
