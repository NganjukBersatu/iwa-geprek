<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'

const props = defineProps<{
  /** Path internal, mis. `/#kontak` atau `/menu`. */
  to: string
}>()

const router = useRouter()
const route = useRoute()

/**
 * - Sudah di halaman yang sama + link hash → scroll halus langsung (tetap bekerja walau hash sama).
 * - Selain itu → router.push (scrollBehavior di router yang mengatur posisi).
 */
async function go(to: string): Promise<void> {
  const target = router.resolve(to)
  if (route.name === target.name && target.hash) {
    document.querySelector(target.hash)?.scrollIntoView() // CSS scroll-behavior + scroll-padding
    window.history.replaceState(window.history.state, '', target.fullPath)
    return
  }
  await router.push(to)
}

function onClick(event: MouseEvent): void {
  // Biarkan browser menangani "buka di tab baru" dsb.
  if (event.defaultPrevented || event.button !== 0) return
  if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return
  event.preventDefault()
  void go(props.to)
}
</script>

<template>
  <a :href="to" @click="onClick"><slot /></a>
</template>