<script setup lang="ts">
import BaseTable from "@/components/ui/BaseTable.vue"
import type { LeadResponse } from "@/types"

defineProps<{
  leads: LeadResponse[]
}>()

const columns = [
  { key: "name", header: "Name" },
  { key: "address", header: "Address" },
  { key: "phone", header: "Phone" },
  { key: "website", header: "Website" },
]
</script>

<template>
  <BaseTable
    :columns="columns"
    :rows="leads"
    empty-text="Waiting for results..."
  >
    <template #cell-website="{ value }">
      <a
        v-if="value && value !== 'N/A'"
        :href="(value as string)"
        target="_blank"
        class="text-blue-600 hover:underline text-xs"
        @click.stop
      >
        {{ value }}
      </a>
      <span v-else class="text-gray-400">N/A</span>
    </template>
  </BaseTable>
</template>
