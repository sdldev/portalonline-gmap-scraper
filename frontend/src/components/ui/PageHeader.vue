<script setup lang="ts">
defineProps<{
  title: string
  subtitle?: string
  showBack?: boolean
}>()

defineEmits<{ back: [] }>()
</script>

<template>
  <div class="flex items-center justify-between mb-6">
    <div class="flex items-center gap-3">
      <button
        v-if="showBack"
        class="p-2 -ml-2 rounded-lg text-gray-500 hover:bg-gray-100 hover:text-gray-700 transition-colors"
        @click="$emit('back')"
      >
        <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
      </button>
      <div>
        <h2 class="text-xl font-bold text-gray-900">{{ title }}</h2>
        <p v-if="subtitle" class="text-sm text-gray-500 mt-0.5">{{ subtitle }}</p>
      </div>
    </div>
    <slot name="actions" />
  </div>
</template>
