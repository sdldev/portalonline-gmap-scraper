<script setup lang="ts">
import BaseButton from "./BaseButton.vue"

defineProps<{
  currentPage: number
  totalPages: number
}>()

defineEmits<{ "page-change": [page: number] }>()
</script>

<template>
  <div
    v-if="totalPages > 1"
    class="flex items-center justify-center gap-4 mt-4"
  >
    <BaseButton
      variant="secondary"
      size="sm"
      :disabled="currentPage <= 1"
      @click="$emit('page-change', currentPage - 1)"
    >
      Previous
    </BaseButton>
    <span class="text-sm text-gray-500">
      Page {{ currentPage }} of {{ totalPages }}
    </span>
    <BaseButton
      variant="secondary"
      size="sm"
      :disabled="currentPage >= totalPages"
      @click="$emit('page-change', currentPage + 1)"
    >
      Next
    </BaseButton>
  </div>
</template>
