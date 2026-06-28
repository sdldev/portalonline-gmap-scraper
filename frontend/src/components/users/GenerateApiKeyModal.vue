<script setup lang="ts">
import { ref } from "vue"
import BaseModal from "@/components/ui/BaseModal.vue"
import BaseButton from "@/components/ui/BaseButton.vue"
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

function copyKey() {
  if (apiKey.value) {
    navigator.clipboard.writeText(apiKey.value)
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
      <!-- Confirm step -->
      <div v-if="!apiKey && !loading">
        <div class="p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-700 mb-4">
          The old API key for <strong>{{ user?.username }}</strong> will be immediately invalidated.
          All services using the old key will stop working.
        </div>
        <div class="flex justify-end gap-2">
          <BaseButton variant="secondary" @click="handleClose">Cancel</BaseButton>
          <BaseButton variant="danger" @click="handleRegenerate">Regenerate</BaseButton>
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
      <div v-if="apiKey" class="space-y-4">
        <div class="p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-800">
          API key regenerated! The old key is no longer valid.
        </div>
        <div class="p-4 bg-gray-50 rounded-lg">
          <p class="text-sm text-gray-600 mb-2">New API key (copy now):</p>
          <div class="flex items-center gap-2">
            <code class="text-xs bg-white px-2 py-1 rounded border flex-1 break-all">{{ apiKey }}</code>
            <BaseButton variant="secondary" size="sm" @click="copyKey">Copy</BaseButton>
          </div>
        </div>
        <BaseButton variant="ghost" size="sm" @click="handleClose">Close</BaseButton>
      </div>
    </div>
  </BaseModal>
</template>
