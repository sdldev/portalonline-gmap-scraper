<script setup lang="ts">
import { ref } from "vue"
import { useRouter } from "vue-router"
import { useAuthStore } from "@/stores/auth"
import BaseButton from "@/components/ui/BaseButton.vue"
import BaseInput from "@/components/ui/BaseInput.vue"
import AlertBanner from "@/components/ui/AlertBanner.vue"

const auth = useAuthStore()
const router = useRouter()

const username = ref("")
const password = ref("")
const loading = ref(false)
const error = ref<string | null>(null)

async function handleSubmit() {
  if (!username.value || !password.value) return
  loading.value = true
  error.value = null
  try {
    await auth.login(username.value, password.value)
    router.push("/dashboard")
  } catch (e: any) {
    error.value = e.response?.data?.detail || "Login failed"
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-100 px-4">
    <div class="w-full max-w-md bg-white rounded-2xl shadow-xl p-8">
      <div class="text-center mb-8">
        <h1 class="text-2xl font-bold text-gray-900">PortalOnline</h1>
        <p class="text-sm text-gray-500 mt-1">GMap Scraper</p>
      </div>

      <form @submit.prevent="handleSubmit" class="space-y-4">
        <AlertBanner v-if="error" variant="error" :message="error" />

        <BaseInput
          v-model="username"
          id="username"
          name="username"
          label="Username"
          required
          placeholder="Enter your username"
        />

        <BaseInput
          v-model="password"
          id="password"
          name="password"
          type="password"
          label="Password"
          required
          placeholder="Enter your password"
        />

        <BaseButton variant="primary" :loading="loading" type="submit" class="w-full">
          Sign In
        </BaseButton>
      </form>
    </div>
  </div>
</template>
