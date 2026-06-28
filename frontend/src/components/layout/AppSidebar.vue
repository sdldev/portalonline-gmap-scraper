<script setup lang="ts">
import { useAuthStore } from "@/stores/auth"
import { useRoute } from "vue-router"

const auth = useAuthStore()
const route = useRoute()

const navItems = [
  { to: "/dashboard", label: "Dashboard", adminOnly: false },
  { to: "/scrape", label: "Scrape", adminOnly: false },
  { to: "/results", label: "Results", adminOnly: false },
  { to: "/users", label: "Users", adminOnly: true },
]

function isActive(path: string): boolean {
  return route.path === path
}
</script>

<template>
  <aside class="w-56 bg-white border-r border-gray-200 flex flex-col shrink-0">
    <nav class="flex-1 py-4">
      <ul class="space-y-1 px-3">
        <li v-for="item in navItems" :key="item.to">
          <template v-if="!item.adminOnly || auth.isAdmin">
            <router-link
              :to="item.to"
              :class="[
                'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                isActive(item.to)
                  ? 'bg-blue-50 text-blue-700'
                  : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900',
              ]"
            >
              {{ item.label }}
            </router-link>
          </template>
        </li>
      </ul>
    </nav>
  </aside>
</template>
