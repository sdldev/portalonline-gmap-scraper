import { createRouter, createWebHistory } from "vue-router"
import { useAuthStore } from "@/stores/auth"
import LoginPage from "@/pages/LoginPage.vue"

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/login",
      name: "login",
      component: LoginPage,
      meta: { guest: true },
    },
    {
      path: "/",
      redirect: "/dashboard",
    },
    {
      path: "/dashboard",
      name: "dashboard",
      component: () => import("@/pages/DashboardPage.vue"),
      meta: { requiresAuth: true },
    },
    {
      path: "/scrape",
      name: "scrape",
      component: () => import("@/pages/ScrapePage.vue"),
      meta: { requiresAuth: true },
    },
    {
      path: "/results",
      name: "results",
      component: () => import("@/pages/ResultsPage.vue"),
      meta: { requiresAuth: true },
    },
    {
      path: "/results/:id",
      name: "job-detail",
      component: () => import("@/pages/JobDetailPage.vue"),
      meta: { requiresAuth: true },
    },
    {
      path: "/users",
      name: "users",
      component: () => import("@/pages/UsersPage.vue"),
      meta: { requiresAuth: true, requiresAdmin: true },
    },
    {
      path: "/users/new",
      name: "user-create",
      component: () => import("@/pages/CreateUserPage.vue"),
      meta: { requiresAuth: true, requiresAdmin: true },
    },
    {
      path: "/users/:id",
      name: "user-detail",
      component: () => import("@/pages/UserDetailPage.vue"),
      meta: { requiresAuth: true, requiresAdmin: true },
    },
    {
      path: "/users/:id/edit",
      name: "user-edit",
      component: () => import("@/pages/UserEditPage.vue"),
      meta: { requiresAuth: true, requiresAdmin: true },
    },
    {
      path: "/:pathMatch(.*)*",
      redirect: "/dashboard",
    },
  ],
})

router.beforeEach((to, _from, next) => {
  const auth = useAuthStore()

  if (to.meta.requiresAuth && !auth.isLoggedIn) {
    return next("/login")
  }

  if (to.meta.requiresAdmin && !auth.isAdmin) {
    return next("/dashboard")
  }

  if (to.meta.guest && auth.isLoggedIn) {
    return next("/dashboard")
  }

  next()
})

export default router
