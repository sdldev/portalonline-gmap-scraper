<script setup lang="ts">
defineProps<{ padding?: string }>()
</script>

<template>
  <div :class="['bg-white rounded-xl shadow-sm border border-gray-200', padding || 'p-6']">
    <slot />
  </div>
</template>
