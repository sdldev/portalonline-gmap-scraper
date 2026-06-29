<script setup lang="ts">
import { useAuthStore } from "@/stores/auth"
import { useRoute, useRouter } from "vue-router"
import { useSidebar } from "@/composables/useSidebar"
import {
  LayoutDashboard,
  Search,
  FileText,
  Users,
  PanelLeftClose,
  PanelLeftOpen,
} from "lucide-vue-next"

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const { collapsed, mobileOpen, isMobile, toggle, closeMobile } = useSidebar()

const navItems = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard, adminOnly: false },
  { to: "/scrape", label: "Scrape", icon: Search, adminOnly: false },
  { to: "/results", label: "Results", icon: FileText, adminOnly: false },
  { to: "/users", label: "Users", icon: Users, adminOnly: true },
]

function isActive(path: string): boolean {
  return route.path.startsWith(path)
}

function handleNav(to: string) {
  router.push(to)
  if (isMobile.value) {
    closeMobile()
  }
}
</script>

<template>
  <!-- Backdrop (mobile only) -->
  <div
    v-if="isMobile && mobileOpen"
    class="fixed inset-0 bg-black/40 z-40 md:hidden"
    @click="closeMobile"
  />

  <aside
    :class="[
      'bg-white border-r border-gray-200 flex flex-col transition-all duration-200',
      isMobile
        ? [
            'fixed inset-y-0 left-0 z-50 w-64 shadow-xl',
            mobileOpen ? 'translate-x-0' : '-translate-x-full',
          ]
        : ['shrink-0', collapsed ? 'w-16' : 'w-56'],
    ]"
  >
    <nav class="flex-1 py-4">
      <ul class="space-y-1 px-2">
        <li v-for="item in navItems" :key="item.to">
          <template v-if="!item.adminOnly || auth.isAdmin">
            <button
              :title="(isMobile || collapsed) ? item.label : undefined"
              :class="[
                'flex items-center w-full rounded-lg text-sm font-medium transition-colors',
                (isMobile || !collapsed) ? 'gap-3 px-3 py-2' : 'justify-center px-2 py-2',
                isActive(item.to)
                  ? 'bg-blue-50 text-blue-700'
                  : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900',
              ]"
              @click="handleNav(item.to)"
            >
              <component :is="item.icon" :size="20" :stroke-width="1.5" />
              <span v-if="isMobile || !collapsed">{{ item.label }}</span>
            </button>
          </template>
        </li>
      </ul>
    </nav>

    <!-- Collapse toggle (desktop only) -->
    <div v-if="!isMobile" class="px-2 pb-4">
      <button
        class="flex items-center justify-center w-full rounded-lg px-2 py-2 text-gray-500 hover:bg-gray-100 hover:text-gray-700 transition-colors"
        @click="toggle"
      >
        <PanelLeftClose v-if="!collapsed" :size="20" :stroke-width="1.5" />
        <PanelLeftOpen v-else :size="20" :stroke-width="1.5" />
      </button>
    </div>
  </aside>
</template>
