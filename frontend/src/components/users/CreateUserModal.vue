<script setup lang="ts">
import { ref } from "vue"
import BaseModal from "@/components/ui/BaseModal.vue"
import BaseButton from "@/components/ui/BaseButton.vue"
import BaseInput from "@/components/ui/BaseInput.vue"
import BaseSelect from "@/components/ui/BaseSelect.vue"
import AlertBanner from "@/components/ui/AlertBanner.vue"
import SecretDisplay from "@/components/ui/SecretDisplay.vue"
import { createUser } from "@/services/users"

defineProps<{ open: boolean }>()
const emit = defineEmits<{ close: []; created: [] }>()

const username = ref("")
const role = ref("user")
const loading = ref(false)
const error = ref<string | null>(null)
const created = ref<{ username: string; api_key: string } | null>(null)

const roleOptions = [
  { value: "user", label: "User" },
  { value: "admin", label: "Admin" },
]

async function handleCreate() {
  if (!username.value.trim()) return
  loading.value = true
  error.value = null
  try {
    const user = await createUser({ username: username.value.trim(), role: role.value })
    created.value = { username: user.username, api_key: user.api_key }
    emit("created")
  } catch (e: any) {
    error.value = e.response?.data?.detail || "Failed to create user"
  } finally {
    loading.value = false
  }
}

function handleClose() {
  username.value = ""
  role.value = "user"
  error.value = null
  created.value = null
  emit("close")
}
</script>

<template>
  <BaseModal :open="open" title="Add User" @close="handleClose">
    <div v-if="created" class="space-y-4">
      <AlertBanner variant="success" :message="`User &quot;${created.username}&quot; created successfully.`" />
      <SecretDisplay
        label="API Key (copy now - won't be shown again)"
        :value="created.api_key"
      />
      <BaseButton variant="ghost" size="sm" @click="handleClose">Close</BaseButton>
    </div>

    <form v-else @submit.prevent="handleCreate" class="space-y-4">
      <AlertBanner v-if="error" variant="error" :message="error" />
      <BaseInput
        v-model="username"
        label="Username"
        required
        :minlength="1"
        :maxlength="50"
        placeholder="only lowercase, numbers, underscore"
      />
      <BaseSelect v-model="role" label="Role" :options="roleOptions" />
      <div class="flex justify-end gap-2">
        <BaseButton variant="secondary" @click="handleClose">Cancel</BaseButton>
        <BaseButton variant="primary" type="submit" :loading="loading">Create</BaseButton>
      </div>
    </form>
  </BaseModal>
</template>
