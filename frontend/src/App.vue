<script setup lang="ts">
import { useAuthStore } from "@/stores/auth"
import { computed } from "vue"
import { useRoute } from "vue-router"
import LoginPage from "@/pages/LoginPage.vue"
import AppLayout from "@/layouts/AppLayout.vue"
import ToastContainer from "@/components/ui/ToastContainer.vue"

const auth = useAuthStore()
const route = useRoute()
const isLoginPage = computed(() => route.name === "login")
</script>

<template>
  <LoginPage v-if="isLoginPage || !auth.isLoggedIn" />
  <AppLayout v-else />
  <ToastContainer />
</template>
