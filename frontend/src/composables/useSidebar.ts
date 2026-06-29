import { ref, computed, onMounted, onUnmounted } from "vue"

const collapsed = ref(false)
const mobileOpen = ref(false)
const isMobile = ref(false)

let resizeHandler: (() => void) | null = null

export function useSidebar() {
  if (!resizeHandler) {
    resizeHandler = () => {
      const wasMobile = isMobile.value
      isMobile.value = window.innerWidth < 768
      if (!isMobile.value && wasMobile) {
        mobileOpen.value = false
      }
    }
    resizeHandler()
    window.addEventListener("resize", resizeHandler)
  }

  function toggle() {
    collapsed.value = !collapsed.value
  }

  function collapse() {
    collapsed.value = true
  }

  function expand() {
    collapsed.value = false
  }

  function openMobile() {
    mobileOpen.value = true
  }

  function closeMobile() {
    mobileOpen.value = false
  }

  function toggleMobile() {
    mobileOpen.value = !mobileOpen.value
  }

  const width = computed(() => (collapsed.value ? "w-16" : "w-56"))

  return {
    collapsed,
    mobileOpen,
    isMobile,
    toggle,
    collapse,
    expand,
    openMobile,
    closeMobile,
    toggleMobile,
    width,
  }
}
