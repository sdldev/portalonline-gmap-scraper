<script setup lang="ts">
import BaseButton from "./BaseButton.vue"
import { copyToClipboard } from "@/utils/formatters"

defineProps<{
  label: string
  value: string
  monospace?: boolean
}>()
</script>

<template>
  <div class="p-4 bg-gray-50 rounded-lg">
    <p class="text-sm text-gray-600 mb-2">{{ label }}:</p>
    <div class="flex items-center gap-2">
      <code
        :class="[
          'bg-white rounded border flex-1',
          monospace
            ? 'text-lg px-3 py-2 font-mono'
            : 'text-xs px-2 py-1 break-all',
        ]"
      >{{ value }}</code>
      <BaseButton variant="secondary" size="sm" @click="copyToClipboard(value)">
        Copy
      </BaseButton>
    </div>
  </div>
</template>
