<script setup lang="ts">
defineProps<{
  rows?: number
  height?: string
  padding?: string
}>()
</script>

<template>
  <div :class="[padding || 'p-6']">
    <div
      v-for="i in (rows || 5)"
      :key="i"
      :class="['bg-gray-200 rounded animate-pulse mb-2', height || 'h-12']"
    />
  </div>
</template>
