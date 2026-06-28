<script setup lang="ts">
import { ref } from "vue"
import { useRouter } from "vue-router"
import { useAuthStore } from "@/stores/auth"
import BaseButton from "@/components/ui/BaseButton.vue"

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
        <!-- Error -->
        <div
          v-if="error"
          class="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700"
        >
          {{ error }}
        </div>

        <div>
          <label for="username" class="block text-sm font-medium text-gray-700 mb-1">
            Username
          </label>
          <input
            id="username"
            v-model="username"
            type="text"
            required
            autofocus
            class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition"
            placeholder="Enter your username"
          />
        </div>

        <div>
          <label for="password" class="block text-sm font-medium text-gray-700 mb-1">
            Password
          </label>
          <input
            id="password"
            v-model="password"
            type="password"
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition"
            placeholder="Enter your password"
          />
        </div>

        <BaseButton variant="primary" :loading="loading" type="submit" class="w-full">
          Sign In
        </BaseButton>
      </form>
    </div>
  </div>
</template>
