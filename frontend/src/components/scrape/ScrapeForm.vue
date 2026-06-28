<script setup lang="ts">
import { ref } from "vue"
import BaseButton from "@/components/ui/BaseButton.vue"

defineProps<{ disabled: boolean }>()
const emit = defineEmits<{ submit: [keyword: string, location: string] }>()

const keyword = ref("")
const location = ref("")

function handleSubmit() {
  if (!keyword.value.trim()) return
  emit("submit", keyword.value.trim(), location.value.trim() || "")
}
</script>

<template>
  <form @submit.prevent="handleSubmit" class="space-y-4">
    <div
      v-if="disabled"
      class="p-3 bg-amber-50 border border-amber-200 rounded-lg text-sm text-amber-700"
    >
      A job is already running. Wait for it to finish before starting a new one.
    </div>
    <div>
      <label for="keyword" class="block text-sm font-medium text-gray-700 mb-1">
        Keyword <span class="text-red-500">*</span>
      </label>
      <input
        id="keyword"
        v-model="keyword"
        type="text"
        required
        maxlength="200"
        autofocus
        :disabled="disabled"
        class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none disabled:bg-gray-100"
        placeholder="e.g. restaurants in jakarta"
      />
    </div>
    <div>
      <label for="location" class="block text-sm font-medium text-gray-700 mb-1">
        Location
      </label>
      <input
        id="location"
        v-model="location"
        type="text"
        maxlength="100"
        :disabled="disabled"
        class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none disabled:bg-gray-100"
        placeholder="e.g. Jakarta"
      />
    </div>
    <BaseButton variant="primary" type="submit" :disabled="disabled">
      Start Scraping
    </BaseButton>
  </form>
</template>
