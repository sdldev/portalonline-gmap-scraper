<script setup lang="ts">
import AppHeader from "@/components/layout/AppHeader.vue"
import AppSidebar from "@/components/layout/AppSidebar.vue"
</script>

<template>
  <div class="h-screen flex flex-col overflow-hidden">
    <AppHeader />
    <div class="flex flex-1 overflow-hidden relative">
      <AppSidebar />
      <main class="flex-1 overflow-y-auto p-4 md:p-6 bg-gray-50">
        <router-view />
      </main>
    </div>
  </div>
</template>
