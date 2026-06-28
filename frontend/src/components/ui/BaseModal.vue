<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from "vue"

const props = defineProps<{
  open: boolean
  title?: string
  size?: "sm" | "md" | "lg"
}>()

const emit = defineEmits<{ close: [] }>()

const dialog = ref<HTMLDialogElement>()

watch(
  () => props.open,
  (val) => {
    if (val) dialog.value?.showModal()
    else dialog.value?.close()
  }
)

function onClose() {
  emit("close")
}

function onBackdropClick(e: MouseEvent) {
  if (e.target === dialog.value) emit("close")
}

onMounted(() => {
  if (props.open) dialog.value?.showModal()
})

function handleKeydown(e: KeyboardEvent) {
  if (e.key === "Escape") emit("close")
}
</script>

<template>
  <dialog
    ref="dialog"
    class="backdrop:bg-black/50 rounded-xl shadow-xl border-0 p-0 max-h-[90vh] overflow-hidden"
    :class="{
      'w-full max-w-sm': size === 'sm',
      'w-full max-w-lg': size === 'md' || !size,
      'w-full max-w-2xl': size === 'lg',
    }"
    @close="onClose"
    @click="onBackdropClick"
    @keydown="handleKeydown"
  >
    <div class="flex flex-col max-h-[90vh]">
      <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200">
        <h3 class="text-lg font-semibold text-gray-900">{{ title }}</h3>
        <button
          class="p-1 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors"
          @click="emit('close')"
        >
          <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      <div class="overflow-y-auto p-6">
        <slot />
      </div>
    </div>
  </dialog>
</template>
