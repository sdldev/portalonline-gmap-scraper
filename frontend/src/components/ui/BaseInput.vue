<script setup lang="ts">
defineProps<{
  modelValue: string
  label?: string
  type?: string
  placeholder?: string
  required?: boolean
  disabled?: boolean
  minlength?: number
  maxlength?: number
  name?: string
  id?: string
}>()

defineEmits<{ "update:modelValue": [value: string] }>()
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
    <input
      :id="id"
      :name="name"
      :type="type || 'text'"
      :value="modelValue"
      :placeholder="placeholder"
      :required="required"
      :disabled="disabled"
      :minlength="minlength"
      :maxlength="maxlength"
      class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none disabled:bg-gray-100 transition"
      @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
    />
  </div>
</template>
