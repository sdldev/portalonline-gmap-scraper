<script setup lang="ts">
import { computed } from "vue"

const props = defineProps<{
  variant: "error" | "success" | "warning" | "info"
  message?: string
}>()

const variantClasses = computed(() => {
  const map = {
    error: "bg-red-50 border-red-200 text-red-700",
    success: "bg-green-50 border-green-200 text-green-800",
    warning: "bg-amber-50 border-amber-200 text-amber-700",
    info: "bg-blue-50 border-blue-200 text-blue-700",
  }
  return map[props.variant]
})
</script>

<template>
  <div :class="['p-3 border rounded-lg text-sm', variantClasses]">
    <slot>{{ message }}</slot>
  </div>
</template>
