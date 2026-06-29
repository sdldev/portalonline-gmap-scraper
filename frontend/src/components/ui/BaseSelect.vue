<script setup lang="ts" generic="T extends string">
defineProps<{
  modelValue: T
  label?: string
  options: { value: T; label: string }[]
  name?: string
  id?: string
}>()

defineEmits<{ "update:modelValue": [value: T] }>()
</script>

<template>
  <div>
    <label
      v-if="label"
      :for="id"
      class="block text-sm font-medium text-gray-700 mb-1"
    >
      {{ label }}
    </label>
    <select
      :id="id"
      :name="name"
      :value="modelValue"
      class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
      @change="$emit('update:modelValue', ($event.target as HTMLSelectElement).value as T)"
    >
      <option v-for="opt in options" :key="opt.value" :value="opt.value">
        {{ opt.label }}
      </option>
    </select>
  </div>
</template>
