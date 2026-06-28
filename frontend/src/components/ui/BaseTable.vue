<script setup lang="ts" generic="T extends Record<string, any>">
defineProps<{
  columns: { key: string; header: string; width?: string; align?: "left" | "right" | "center" }[]
  rows: T[]
  loading?: boolean
  emptyText?: string
}>()

defineEmits<{ rowClick: [row: T] }>()
</script>

<template>
  <div class="overflow-x-auto">
    <table class="min-w-full divide-y divide-gray-200">
      <thead class="bg-gray-50">
        <tr>
          <th
            v-for="col in columns"
            :key="col.key"
            :style="{ width: col.width, textAlign: col.align || 'left' }"
            class="px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider"
          >
            {{ col.header }}
          </th>
        </tr>
      </thead>
      <tbody class="bg-white divide-y divide-gray-100">
        <!-- Loading -->
        <tr v-if="loading" v-for="i in 5" :key="'skeleton-' + i">
          <td v-for="col in columns" :key="col.key" class="px-4 py-3">
            <div class="h-4 bg-gray-200 rounded animate-pulse" />
          </td>
        </tr>
        <!-- Empty -->
        <tr v-else-if="rows.length === 0">
          <td :colspan="columns.length" class="px-4 py-12 text-center text-gray-500">
            {{ emptyText || "No data available" }}
          </td>
        </tr>
        <!-- Data -->
        <tr
          v-else
          v-for="(row, idx) in rows"
          :key="idx"
          class="hover:bg-gray-50 cursor-pointer transition-colors"
          @click="$emit('rowClick', row)"
        >
          <td
            v-for="col in columns"
            :key="col.key"
            :style="{ textAlign: col.align || 'left' }"
            class="px-4 py-3 text-sm"
          >
            <slot :name="'cell-' + col.key" :row="row" :value="row[col.key]">
              {{ row[col.key] }}
            </slot>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
