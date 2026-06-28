<script setup lang="ts">
import { computed } from "vue"

const props = defineProps<{
  variant?: "default" | "success" | "warning" | "danger" | "info"
}>()

const colorMap: Record<string, string> = {
  default: "bg-gray-100 text-gray-700",
  success: "bg-green-100 text-green-800",
  warning: "bg-amber-100 text-amber-800",
  danger: "bg-red-100 text-red-800",
  info: "bg-blue-100 text-blue-800",
}

const classes = computed(() => colorMap[props.variant || "default"])
</script>

<template>
  <span :class="['inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium', classes]">
    <slot />
  </span>
</template>
