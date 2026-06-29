<script setup lang="ts">
import { ref } from "vue"
import { Search, MapPin, Play } from "lucide-vue-next"
import BaseButton from "@/components/ui/BaseButton.vue"
import BaseInput from "@/components/ui/BaseInput.vue"
import AlertBanner from "@/components/ui/AlertBanner.vue"

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
    <AlertBanner v-if="disabled" variant="warning">
      <span class="flex items-center gap-2">
        <Search :size="16" :stroke-width="1.5" class="shrink-0" />
        A job is already running. Wait for it to finish before starting a new one.
      </span>
    </AlertBanner>
    <div>
      <label for="keyword" class="flex items-center gap-1.5 text-sm font-medium text-gray-700 mb-1.5">
        <Search :size="14" :stroke-width="1.5" class="text-gray-400" />
        Keyword <span class="text-red-500">*</span>
      </label>
      <input
        id="keyword"
        v-model="keyword"
        name="keyword"
        type="text"
        required
        maxlength="200"
        autofocus
        :disabled="disabled"
        class="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none disabled:bg-gray-100 transition-shadow"
        placeholder="e.g. restaurants in jakarta"
      />
    </div>
    <div>
      <label for="location" class="flex items-center gap-1.5 text-sm font-medium text-gray-700 mb-1.5">
        <MapPin :size="14" :stroke-width="1.5" class="text-gray-400" />
        Location <span class="text-gray-400 font-normal">(optional)</span>
      </label>
      <input
        id="location"
        v-model="location"
        name="location"
        type="text"
        maxlength="100"
        :disabled="disabled"
        class="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none disabled:bg-gray-100 transition-shadow"
        placeholder="e.g. Jakarta"
      />
    </div>
    <BaseButton variant="primary" type="submit" :disabled="disabled" class="gap-2">
      <Play :size="16" :stroke-width="1.5" />
      Start Scraping
    </BaseButton>
  </form>
</template>
