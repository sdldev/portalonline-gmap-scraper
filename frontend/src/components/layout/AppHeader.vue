<script setup lang="ts">
import { useAuthStore } from "@/stores/auth"
import { useRouter } from "vue-router"

const auth = useAuthStore()
const router = useRouter()

async function handleLogout() {
  await auth.logout()
  router.push("/login")
}
</script>

<template>
  <header class="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6 shrink-0">
    <div class="flex items-center gap-3">
      <h1 class="text-lg font-bold text-gray-900">PortalOnline</h1>
      <span class="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded">GMap Scraper</span>
    </div>
    <div class="flex items-center gap-4">
      <span class="text-sm text-gray-600">
        {{ auth.username }}
        <span class="text-xs text-gray-400 ml-1">({{ auth.user?.role }})</span>
      </span>
      <button
        class="text-sm text-gray-500 hover:text-gray-700 transition-colors"
        @click="handleLogout"
      >
        Logout
      </button>
    </div>
  </header>
</template>
