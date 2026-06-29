<script setup lang="ts">
import BaseTable from "@/components/ui/BaseTable.vue"
import { Star, Phone, Globe, MapPin } from "lucide-vue-next"
import type { LeadResponse } from "@/types"

defineProps<{
  leads: LeadResponse[]
}>()

const columns = [
  { key: "name", header: "Name" },
  { key: "address", header: "Address" },
  { key: "phone", header: "Phone" },
  { key: "website", header: "Website" },
  { key: "rating", header: "Rating", width: "80px", align: "center" as const },
]
</script>

<template>
  <BaseTable
    :columns="columns"
    :rows="leads"
    empty-text="Waiting for results..."
  >
    <template #cell-name="{ value }">
      <span class="font-medium text-gray-900">{{ value }}</span>
    </template>
    <template #cell-address="{ value }">
      <span class="flex items-center gap-1 text-gray-500">
        <MapPin :size="12" :stroke-width="1.5" class="shrink-0 text-gray-400" />
        {{ value }}
      </span>
    </template>
    <template #cell-phone="{ value }">
      <span v-if="value && value !== 'N/A'" class="flex items-center gap-1">
        <Phone :size="12" :stroke-width="1.5" class="shrink-0 text-gray-400" />
        {{ value }}
      </span>
      <span v-else class="text-gray-400">N/A</span>
    </template>
    <template #cell-website="{ value }">
      <a
        v-if="value && value !== 'N/A'"
        :href="(value as string)"
        target="_blank"
        class="flex items-center gap-1 text-blue-600 hover:underline"
        @click.stop
      >
        <Globe :size="12" :stroke-width="1.5" class="shrink-0" />
        <span class="truncate max-w-[150px]">{{ value }}</span>
      </a>
      <span v-else class="text-gray-400">N/A</span>
    </template>
    <template #cell-rating="{ value, row }">
      <span v-if="value && value !== 'N/A'" class="flex items-center gap-1 justify-center">
        <Star :size="12" :stroke-width="1.5" class="text-amber-400 fill-amber-400" />
        <span class="text-sm font-medium">{{ value }}</span>
        <span class="text-xs text-gray-400">({{ row.review_count }})</span>
      </span>
      <span v-else class="text-gray-400">-</span>
    </template>
  </BaseTable>
</template>
