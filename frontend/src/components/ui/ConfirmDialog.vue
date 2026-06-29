<script setup lang="ts">
import { watch, ref, onMounted } from "vue"

const props = defineProps<{
  open: boolean
  title: string
  message: string
  confirmLabel?: string
  variant?: "danger" | "warning"
}>()

const emit = defineEmits<{ confirm: []; cancel: [] }>()

const dialog = ref<HTMLDialogElement>()

watch(
  () => props.open,
  (val) => {
    if (val) dialog.value?.showModal()
    else dialog.value?.close()
  }
)

onMounted(() => {
  if (props.open) dialog.value?.showModal()
})

function onClose() {
  emit("cancel")
}

function onBackdropClick(e: MouseEvent) {
  if (e.target === dialog.value) emit("cancel")
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === "Escape") emit("cancel")
}
</script>

<template>
  <dialog
    ref="dialog"
    class="backdrop:bg-black/50 rounded-xl shadow-xl border-0 p-0 w-full max-w-sm fixed inset-0 m-auto h-fit"
    @close="onClose"
    @click="onBackdropClick"
    @keydown="handleKeydown"
  >
    <div class="p-6">
      <h3 class="text-lg font-semibold text-gray-900 mb-2">{{ title }}</h3>
      <p class="text-sm text-gray-600 mb-6">{{ message }}</p>
      <div class="flex justify-end gap-2">
        <button
          class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          @click="emit('cancel')"
        >
          Cancel
        </button>
        <button
          :class="[
            'px-4 py-2 text-sm font-medium text-white rounded-lg transition-colors',
            variant === 'danger' ? 'bg-red-600 hover:bg-red-700' : 'bg-amber-600 hover:bg-amber-700',
          ]"
          @click="emit('confirm')"
        >
          {{ confirmLabel || "Confirm" }}
        </button>
      </div>
    </div>
  </dialog>
</template>
