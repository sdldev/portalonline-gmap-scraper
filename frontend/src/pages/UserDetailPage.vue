<script setup lang="ts">
import { ref, onMounted } from "vue"
import { useRoute, useRouter } from "vue-router"
import { getUser, deleteUser, generatePassword, generateApiKey } from "@/services/users"
import BaseButton from "@/components/ui/BaseButton.vue"
import BaseBadge from "@/components/ui/BaseBadge.vue"
import BaseCard from "@/components/ui/BaseCard.vue"
import AlertBanner from "@/components/ui/AlertBanner.vue"
import PageHeader from "@/components/ui/PageHeader.vue"
import SkeletonLoader from "@/components/ui/SkeletonLoader.vue"
import SecretDisplay from "@/components/ui/SecretDisplay.vue"
import ConfirmDialog from "@/components/ui/ConfirmDialog.vue"
import { copyToClipboard } from "@/utils/formatters"
import type { UserResponse } from "@/types"

const route = useRoute()
const router = useRouter()
const userId = route.params.id as string

const user = ref<UserResponse | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)

const deleteConfirmOpen = ref(false)
const apiKeyConfirmOpen = ref(false)

const passwordLoading = ref(false)
const passwordResult = ref<string | null>(null)
const passwordError = ref<string | null>(null)

const apiKeyLoading = ref(false)
const apiKeyResult = ref<string | null>(null)
const apiKeyError = ref<string | null>(null)

async function loadUser() {
  loading.value = true
  error.value = null
  try {
    user.value = await getUser(userId)
  } catch (e: any) {
    error.value = e.response?.data?.detail || "Failed to load user"
  } finally {
    loading.value = false
  }
}

onMounted(loadUser)

async function confirmDelete() {
  if (!user.value) return
  try {
    await deleteUser(user.value.user_id)
    router.push("/users")
  } catch (e: any) {
    alert(e.response?.data?.detail || "Delete failed")
  } finally {
    deleteConfirmOpen.value = false
  }
}

async function handleGeneratePassword() {
  if (!user.value) return
  passwordLoading.value = true
  passwordError.value = null
  passwordResult.value = null
  try {
    const result = await generatePassword(user.value.user_id)
    passwordResult.value = result.password
  } catch (e: any) {
    passwordError.value = e.response?.data?.detail || "Failed to generate password"
  } finally {
    passwordLoading.value = false
  }
}

async function confirmGenerateApiKey() {
  if (!user.value) return
  apiKeyLoading.value = true
  apiKeyError.value = null
  apiKeyResult.value = null
  apiKeyConfirmOpen.value = false
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
    <PageHeader title="User Details" show-back @back="router.push('/users')" />

    <BaseCard v-if="loading" padding="p-0">
      <SkeletonLoader :rows="6" height="h-8" />
    </BaseCard>

    <AlertBanner v-else-if="error && !user" variant="error" class="mb-4">
      {{ error }}
      <BaseButton variant="secondary" size="sm" class="ml-2" @click="loadUser">Retry</BaseButton>
    </AlertBanner>

    <template v-else-if="user">
      <BaseCard>
        <h3 class="text-lg font-semibold text-gray-900 mb-4">User Information</h3>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
          <div>
            <span class="text-gray-500">Username:</span>
            <span class="ml-1 font-medium">{{ user.username }}</span>
          </div>
          <div>
            <span class="text-gray-500">Role:</span>
            <BaseBadge :variant="user.role === 'admin' ? 'info' : 'default'" class="ml-1">
              {{ user.role }}
            </BaseBadge>
          </div>
          <div>
            <span class="text-gray-500">Status:</span>
            <BaseBadge :variant="user.active ? 'success' : 'danger'" class="ml-1">
              {{ user.active ? 'Active' : 'Inactive' }}
            </BaseBadge>
          </div>
          <div>
            <span class="text-gray-500">User ID:</span>
            <code class="ml-1 text-xs bg-gray-100 px-1 rounded">{{ user.user_id }}</code>
          </div>
          <div class="sm:col-span-2">
            <SecretDisplay label="API Key" :value="user.api_key" />
          </div>
          <div>
            <span class="text-gray-500">Created:</span>
            <span class="ml-1">{{ new Date(user.created_at).toLocaleString() }}</span>
          </div>
          <div>
            <span class="text-gray-500">Webhook:</span>
            <span class="ml-1">{{ user.webhook_url || "Not set" }}</span>
          </div>
        </div>
        <div class="flex gap-2 mt-6 pt-4 border-t border-gray-200">
          <BaseButton variant="primary" size="sm" @click="router.push(`/users/${user.user_id}/edit`)">
            Edit
          </BaseButton>
          <BaseButton variant="danger" size="sm" @click="deleteConfirmOpen = true">
            Delete
          </BaseButton>
        </div>
      </BaseCard>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-4">
        <BaseCard>
          <h3 class="text-lg font-semibold text-gray-900 mb-4">Generate Password</h3>
          <p class="text-sm text-gray-600 mb-3">Generate a new random password for this user.</p>
          <AlertBanner v-if="passwordError" variant="error" :message="passwordError" class="mb-3" />
          <SecretDisplay
            v-if="passwordResult"
            label="New password (copy now)"
            :value="passwordResult"
            monospace
            class="mb-3"
          />
          <BaseButton
            variant="primary"
            size="sm"
            :loading="passwordLoading"
            @click="handleGeneratePassword"
          >
            Generate
          </BaseButton>
        </BaseCard>

        <BaseCard>
          <h3 class="text-lg font-semibold text-gray-900 mb-4">Regenerate API Key</h3>
          <AlertBanner variant="warning" message="The old API key will be immediately invalidated." class="mb-3" />
          <AlertBanner v-if="apiKeyError" variant="error" :message="apiKeyError" class="mb-3" />
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
            Regenerate
          </BaseButton>
        </BaseCard>
      </div>
    </template>

    <ConfirmDialog
      :open="deleteConfirmOpen"
      title="Delete User"
      :message="`Delete user \&quot;${user?.username}\&quot;?`"
      confirm-label="Delete"
      variant="danger"
      @confirm="confirmDelete"
      @cancel="deleteConfirmOpen = false"
    />
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
