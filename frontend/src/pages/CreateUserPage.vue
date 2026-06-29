<script setup lang="ts">
import { ref } from "vue"
import { useRouter } from "vue-router"
import { createUser } from "@/services/users"
import BaseButton from "@/components/ui/BaseButton.vue"
import BaseCard from "@/components/ui/BaseCard.vue"
import BaseInput from "@/components/ui/BaseInput.vue"
import BaseSelect from "@/components/ui/BaseSelect.vue"
import AlertBanner from "@/components/ui/AlertBanner.vue"
import PageHeader from "@/components/ui/PageHeader.vue"
import SecretDisplay from "@/components/ui/SecretDisplay.vue"

const router = useRouter()

const username = ref("")
const role = ref("user")
const password = ref("")
const loading = ref(false)
const error = ref<string | null>(null)
const created = ref<{ username: string; api_key: string; user_id: string; password: string } | null>(null)

const roleOptions = [
  { value: "user", label: "User" },
  { value: "admin", label: "Admin" },
]

function generatePassword() {
  const chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%&*"
  let result = ""
  const arr = new Uint32Array(16)
  crypto.getRandomValues(arr)
  for (const n of arr) {
    result += chars[n % chars.length]
  }
  password.value = result
}

async function handleCreate() {
  if (!username.value.trim()) return
  loading.value = true
  error.value = null
  try {
    const user = await createUser({
      username: username.value.trim(),
      role: role.value,
      password: password.value || undefined,
    })
    created.value = {
      username: user.username,
      api_key: user.api_key,
      user_id: user.user_id,
      password: password.value || "(auto-generated)",
    }
  } catch (e: any) {
    error.value = e.response?.data?.detail || "Failed to create user"
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div>
    <PageHeader title="Add User" show-back @back="router.push('/users')" />

    <BaseCard v-if="created">
      <AlertBanner variant="success" :message="`User &quot;${created.username}&quot; created successfully.`" class="mb-4" />
      <div class="space-y-3 mb-4">
        <SecretDisplay
          v-if="created.password !== '(auto-generated)'"
          label="Password"
          :value="created.password"
          monospace
        />
        <SecretDisplay
          label="API Key (copy now, won't be shown again)"
          :value="created.api_key"
        />
      </div>
      <div class="flex gap-2">
        <BaseButton variant="primary" size="sm" @click="router.push(`/users/${created.user_id}`)">
          View User
        </BaseButton>
        <BaseButton variant="ghost" size="sm" @click="router.push('/users')">
          Back to Users
        </BaseButton>
      </div>
    </BaseCard>

    <BaseCard v-else>
      <form @submit.prevent="handleCreate" class="space-y-4 max-w-lg">
        <AlertBanner v-if="error" variant="error" :message="error" />
        <BaseInput
          v-model="username"
          id="create-username"
          name="username"
          label="Username"
          required
          :minlength="1"
          :maxlength="50"
          placeholder="only lowercase, numbers, underscore"
        />
        <BaseSelect
          v-model="role"
          id="create-role"
          name="role"
          label="Role"
          :options="roleOptions"
        />
        <div>
          <label for="create-password" class="block text-sm font-medium text-gray-700 mb-1">Password</label>
          <div class="flex gap-2">
            <input
              id="create-password"
              v-model="password"
              name="password"
              type="text"
              minlength="8"
              placeholder="Min 8 characters (leave empty for auto-generate)"
              class="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
            />
            <BaseButton variant="secondary" size="sm" type="button" @click="generatePassword">
              Generate
            </BaseButton>
          </div>
        </div>
        <div class="flex gap-2 pt-4 border-t border-gray-200">
          <BaseButton variant="primary" type="submit" :loading="loading">Create</BaseButton>
          <BaseButton variant="secondary" @click="router.push('/users')">Cancel</BaseButton>
        </div>
      </form>
    </BaseCard>
  </div>
</template>
