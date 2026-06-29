<script setup lang="ts">
import { ref, onMounted } from "vue"
import { useRoute, useRouter } from "vue-router"
import { getUser, updateUser, updatePassword, generateApiKey } from "@/services/users"
import BaseButton from "@/components/ui/BaseButton.vue"
import BaseCard from "@/components/ui/BaseCard.vue"
import BaseInput from "@/components/ui/BaseInput.vue"
import BaseSelect from "@/components/ui/BaseSelect.vue"
import AlertBanner from "@/components/ui/AlertBanner.vue"
import PageHeader from "@/components/ui/PageHeader.vue"
import SkeletonLoader from "@/components/ui/SkeletonLoader.vue"
import SecretDisplay from "@/components/ui/SecretDisplay.vue"
import ConfirmDialog from "@/components/ui/ConfirmDialog.vue"
import type { UserResponse } from "@/types"

const route = useRoute()
const router = useRouter()
const userId = route.params.id as string

const user = ref<UserResponse | null>(null)
const loading = ref(true)
const saving = ref(false)
const error = ref<string | null>(null)

const username = ref("")
const role = ref("user")
const active = ref(true)

const newPassword = ref("")
const passwordSaving = ref(false)
const passwordSuccess = ref(false)
const passwordError = ref<string | null>(null)

const apiKeyLoading = ref(false)
const apiKeyResult = ref<string | null>(null)
const apiKeyError = ref<string | null>(null)
const apiKeyConfirmOpen = ref(false)

const roleOptions = [
  { value: "user", label: "User" },
  { value: "admin", label: "Admin" },
]

async function loadUser() {
  loading.value = true
  error.value = null
  try {
    user.value = await getUser(userId)
    username.value = user.value.username
    role.value = user.value.role
    active.value = user.value.active
  } catch (e: any) {
    error.value = e.response?.data?.detail || "Failed to load user"
  } finally {
    loading.value = false
  }
}

onMounted(loadUser)

async function handleUpdate() {
  if (!user.value) return
  saving.value = true
  error.value = null
  try {
    await updateUser(user.value.user_id, {
      username: username.value.trim() || undefined,
      role: role.value,
      active: active.value,
    })
    router.push(`/users/${user.value.user_id}`)
  } catch (e: any) {
    error.value = e.response?.data?.detail || "Failed to update user"
  } finally {
    saving.value = false
  }
}

async function handleUpdatePassword() {
  if (!user.value || !newPassword.value.trim()) return
  passwordSaving.value = true
  passwordError.value = null
  passwordSuccess.value = false
  try {
    await updatePassword(user.value.user_id, newPassword.value)
    passwordSuccess.value = true
    newPassword.value = ""
  } catch (e: any) {
    passwordError.value = e.response?.data?.detail || "Failed to update password"
  } finally {
    passwordSaving.value = false
  }
}

async function confirmGenerateApiKey() {
  if (!user.value) return
  apiKeyConfirmOpen.value = false
  apiKeyLoading.value = true
  apiKeyError.value = null
  apiKeyResult.value = null
  try {
    const result = await generateApiKey(user.value.user_id)
    apiKeyResult.value = result.api_key
    await loadUser()
  } catch (e: any) {
    apiKeyError.value = e.response?.data?.detail || "Failed to regenerate API key"
  } finally {
    apiKeyLoading.value = false
  }
}
</script>

<template>
  <div>
    <PageHeader title="Edit User" show-back @back="router.back()" />

    <BaseCard v-if="loading" padding="p-0">
      <SkeletonLoader :rows="4" height="h-10" />
    </BaseCard>

    <AlertBanner v-else-if="error && !user" variant="error" class="mb-4">
      {{ error }}
      <BaseButton variant="secondary" size="sm" class="ml-2" @click="loadUser">Retry</BaseButton>
    </AlertBanner>

    <BaseCard v-else-if="user" class="mb-4">
      <h3 class="text-lg font-semibold text-gray-900 mb-4">User Information</h3>
      <form @submit.prevent="handleUpdate" class="space-y-4 max-w-lg">
        <AlertBanner v-if="error" variant="error" :message="error" />
        <BaseInput
          v-model="username"
          id="edit-username"
          name="username"
          label="Username"
          required
        />
        <BaseSelect
          v-model="role"
          id="edit-role"
          name="role"
          label="Role"
          :options="roleOptions"
        />
        <div class="flex items-center gap-2">
          <input id="active-toggle" v-model="active" name="active" type="checkbox" class="rounded" />
          <label for="active-toggle" class="text-sm text-gray-700">Active</label>
        </div>
        <div class="flex gap-2 pt-4 border-t border-gray-200">
          <BaseButton variant="primary" type="submit" :loading="saving">Save</BaseButton>
          <BaseButton variant="secondary" @click="router.back()">Cancel</BaseButton>
        </div>
      </form>
    </BaseCard>

    <div v-if="user" class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <BaseCard>
        <h3 class="text-lg font-semibold text-gray-900 mb-4">Update Password</h3>
        <form @submit.prevent="handleUpdatePassword" class="space-y-3">
          <AlertBanner v-if="passwordError" variant="error" :message="passwordError" />
          <AlertBanner v-if="passwordSuccess" variant="success" message="Password updated successfully." />
          <BaseInput
            v-model="newPassword"
            id="edit-password"
            name="new_password"
            type="password"
            label="New Password"
            required
            :minlength="8"
            placeholder="Min 8 characters"
          />
          <BaseButton variant="primary" size="sm" type="submit" :loading="passwordSaving">
            Update Password
          </BaseButton>
        </form>
      </BaseCard>

      <BaseCard>
        <h3 class="text-lg font-semibold text-gray-900 mb-4">Regenerate API Key</h3>
        <AlertBanner variant="warning" message="The old API key will be immediately invalidated." class="mb-3" />
        <AlertBanner v-if="apiKeyError" variant="error" :message="apiKeyError" />
        <SecretDisplay
          v-if="apiKeyResult"
          label="New API key (copy now)"
          :value="apiKeyResult"
          class="mb-3"
        />
        <BaseButton
          variant="danger"
          size="sm"
          :loading="apiKeyLoading"
          @click="apiKeyConfirmOpen = true"
        >
          Regenerate API Key
        </BaseButton>
      </BaseCard>
    </div>

    <ConfirmDialog
      :open="apiKeyConfirmOpen"
      title="Regenerate API Key"
      message="The old API key will be immediately invalidated. All services using the old key will stop working."
      confirm-label="Regenerate"
      variant="warning"
      @confirm="confirmGenerateApiKey"
      @cancel="apiKeyConfirmOpen = false"
    />
  </div>
</template>
