<script setup lang="ts">
import BaseModal from "@/components/ui/BaseModal.vue"
import BaseBadge from "@/components/ui/BaseBadge.vue"
import BaseButton from "@/components/ui/BaseButton.vue"
import type { UserResponse } from "@/types"

defineProps<{
  open: boolean
  user: UserResponse | null
}>()

const emit = defineEmits<{ close: [] }>()

function copyText(text: string) {
  navigator.clipboard.writeText(text)
}
</script>

<template>
  <BaseModal :open="open" title="User Details" @close="emit('close')">
    <div v-if="user" class="space-y-3">
      <div class="grid grid-cols-2 gap-3 text-sm">
        <div>
          <span class="text-gray-500">Username:</span>
          <span class="ml-1 font-medium">{{ user.username }}</span>
        </div>
        <div>
          <span class="text-gray-500">Role:</span>
          <BaseBadge :variant="user.role === 'admin' ? 'info' : 'default'" class="ml-1">
            {{ user.role }}
          </BaseBadge>
        </div>
        <div>
          <span class="text-gray-500">Status:</span>
          <BaseBadge :variant="user.active ? 'success' : 'danger'" class="ml-1">
            {{ user.active ? 'Active' : 'Inactive' }}
          </BaseBadge>
        </div>
        <div>
          <span class="text-gray-500">User ID:</span>
          <code class="ml-1 text-xs bg-gray-100 px-1 rounded">{{ user.user_id }}</code>
        </div>
        <div class="col-span-2">
          <span class="text-gray-500">API Key:</span>
          <div class="flex items-center gap-2 mt-1">
            <code class="text-xs bg-gray-100 px-2 py-1 rounded flex-1 break-all">{{ user.api_key }}</code>
            <BaseButton variant="ghost" size="sm" @click="copyText(user.api_key)">Copy</BaseButton>
          </div>
        </div>
        <div>
          <span class="text-gray-500">Created:</span>
          <span class="ml-1">{{ new Date(user.created_at).toLocaleString() }}</span>
        </div>
        <div>
          <span class="text-gray-500">Webhook:</span>
          <span class="ml-1">{{ user.webhook_url || "Not set" }}</span>
        </div>
      </div>
      <div class="flex justify-end pt-4 border-t border-gray-200">
        <BaseButton variant="ghost" @click="emit('close')">Close</BaseButton>
      </div>
    </div>
  </BaseModal>
</template>
