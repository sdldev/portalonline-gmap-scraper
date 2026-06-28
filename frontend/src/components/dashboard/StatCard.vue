<script setup lang="ts">
defineProps<{
  label: string
  value: number | string
}>()
</script>

<template>
  <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
    <p class="text-sm text-gray-500 mb-1">{{ label }}</p>
    <p class="text-2xl font-bold text-gray-900">{{ value }}</p>
  </div>
</template>
