<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Utensils } from 'lucide-vue-next'
import AnchorLink from '@/components/AnchorLink.vue'
import logo from '@/assets/images/logo.jpeg'
import { business, navLinks, type NavKey } from '@/data/site'

const route = useRoute()
const activeKey = ref<NavKey>('beranda')
const menuOpen = ref(false)
const linksEl = ref<HTMLElement | null>(null)

// ===== Efek halaman: scroll spy (hanya di Beranda; di halaman Menu, "Menu Andalan" selalu aktif) =====
/** Urutan section di Beranda (atas → bawah). */
const spySections: { elementId: string; key: NavKey }[] = [
  { elementId: 'beranda', key: 'beranda' },
  { elementId: 'keunggulan', key: 'keunggulan' },
  { elementId: 'menu-preview', key: 'menu' },
  { elementId: 'kontak', key: 'kontak' },
  { elementId: 'karier', key: 'karier' },
]

/** Section aktif = section terakhir yang bagian atasnya sudah melewati 40% tinggi layar. */
function spy(): void {
  if (route.name !== 'home') return
  const line = window.innerHeight * 0.4
  let current: NavKey = 'beranda'
  for (const { elementId, key } of spySections) {
    const el = document.getElementById(elementId)
    if (el && el.getBoundingClientRect().top <= line) current = key
  }
  activeKey.value = current
}

// ===== Efek navbar: sticky shrink + scroll progress bar =====
/** Setelah scroll lebih dari nilai ini (px) navbar mengecil (.scrolled). */
const SHRINK_AFTER = 24
const scrolled = ref(false)
const progress = ref(0)

function tick(): void {
  const y = window.scrollY
  const max = document.documentElement.scrollHeight - window.innerHeight
  scrolled.value = y > SHRINK_AFTER
  progress.value = max > 0 ? Math.min(1, y / max) : 0
}

// ===== Efek navbar: sliding pill / magic line (desktop saja) =====
/** Di bawah lebar ini (px) navbar memakai layout mobile → pill dimatikan. */
const DESKTOP_MIN = 901
const pillActive = ref(false)
const pillReady = ref(false)
const pillStyle = ref({ width: '0px', transform: 'translateX(0px)', opacity: 0 })

function updatePill(): void {
  const ul = linksEl.value
  if (!ul) return
  if (window.innerWidth < DESKTOP_MIN) {
    pillActive.value = false
    pillReady.value = false
    return
  }
  const link = ul.querySelector<HTMLElement>('a.on')
  if (!link) {
    pillStyle.value = { ...pillStyle.value, opacity: 0 }
    return
  }
  pillStyle.value = {
    width: `${link.offsetWidth}px`,
    transform: `translateX(${link.offsetLeft}px)`,
    opacity: 1,
  }
  if (!pillActive.value) {
    pillActive.value = true
    requestAnimationFrame(() => requestAnimationFrame(() => (pillReady.value = true)))
  }
}

watch(activeKey, () => nextTick(updatePill))

watch(
  () => route.name,
  (name) => {
    menuOpen.value = false
    if (name === 'menu') activeKey.value = 'menu'
    else void nextTick(spy)
  },
  { immediate: true },
)

function onScroll(): void {
  tick()
  spy()
}
function onResizeOrLoad(): void {
  tick()
  spy()
  updatePill()
}

function onLinkClick(key: NavKey): void {
  menuOpen.value = false
  activeKey.value = key
}

onMounted(() => {
  tick()
  spy()
  updatePill()
  window.addEventListener('scroll', onScroll, { passive: true })
  window.addEventListener('resize', onResizeOrLoad)
  window.addEventListener('load', onResizeOrLoad)
  void document.fonts?.ready.then(updatePill)
})
onBeforeUnmount(() => {
  window.removeEventListener('scroll', onScroll)
  window.removeEventListener('resize', onResizeOrLoad)
  window.removeEventListener('load', onResizeOrLoad)
})
</script>

<template>
  <nav :class="{ scrolled }" aria-label="Navigasi utama">
    <AnchorLink class="brand" to="/#beranda" @click="onLinkClick('beranda')">
      <span class="mark"><img :src="logo" alt="Logo Iwageprek" /></span>
      <span class="word">
        <b>IWA<i>GEPREK</i></b>
        <small>{{ business.tagline }}</small>
      </span>
    </AnchorLink>

    <ul
      id="nav-links"
      ref="linksEl"
      class="links"
      :class="{ open: menuOpen, 'has-pill': pillActive, ready: pillReady }"
    >
      <li class="pillbg" aria-hidden="true" :style="pillStyle"></li>
      <li v-for="link in navLinks" :key="link.key">
        <AnchorLink
          :to="link.to"
          :class="{ on: activeKey === link.key }"
          :aria-current="activeKey === link.key ? 'page' : undefined"
          @click="onLinkClick(link.key)"
        >
          {{ link.label }}
        </AnchorLink>
      </li>
    </ul>

    <AnchorLink class="btn" to="/#kontak" @click="onLinkClick('kontak')">
      <Utensils class="ic" aria-hidden="true" /> Pesan Sekarang
    </AnchorLink>

    <button
      class="burger"
      type="button"
      aria-label="Menu"
      aria-controls="nav-links"
      :aria-expanded="menuOpen"
      @click="menuOpen = !menuOpen"
    >
      ☰
    </button>

    <!-- Efek navbar: scroll progress bar -->
    <i class="prog" aria-hidden="true" :style="{ transform: `scaleX(${progress})` }"></i>
  </nav>
</template>

<style scoped>
nav {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 5vw;
  background: #fdfdfd;
  /* Efek navbar: smooth transition saat shrink */
  transition:
    padding 0.3s,
    background 0.3s,
    box-shadow 0.3s,
    backdrop-filter 0.3s;
}
/* Efek navbar: sticky shrink + glassmorphism */
nav.scrolled {
  padding-top: 8px;
  padding-bottom: 8px;
  background: rgba(253, 253, 253, 0.82);
  -webkit-backdrop-filter: saturate(180%) blur(14px);
  backdrop-filter: saturate(180%) blur(14px);
  box-shadow: 0 10px 30px rgba(1, 93, 247, 0.14);
}
/* Efek navbar: logo scale-down (titik tumpu kiri) */
nav .brand {
  transition: transform 0.3s;
  transform-origin: left center;
}
nav.scrolled .brand {
  transform: scale(0.9);
}

/* Efek navbar: scroll progress bar */
.prog {
  position: absolute;
  left: 0;
  bottom: 0;
  width: 100%;
  height: 3px;
  background: linear-gradient(90deg, var(--red), var(--sky));
  transform: scaleX(0);
  transform-origin: left;
  transition: transform 0.12s linear;
  pointer-events: none;
}

.links {
  display: flex;
  gap: 6px;
  list-style: none;
  padding: 0;
  position: relative;
}
.links a {
  display: block;
  padding: 10px 18px;
  border-radius: 99px;
  text-decoration: none;
  color: var(--blue);
  font-weight: 500;
  font-size: 0.95rem;
  /* Efek navbar: smooth color transition */
  transition:
    color 0.3s,
    background 0.25s,
    transform 0.2s;
}
/* Efek hover: background highlight */
.links a:hover {
  background: rgba(8, 152, 232, 0.12);
}
.links a.on {
  background: var(--red);
  color: #fff;
  position: relative;
}

.pillbg {
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  border-radius: 99px;
  background: var(--red);
  box-shadow: 0 8px 18px rgba(204, 11, 20, 0.35);
  pointer-events: none;
  opacity: 0;
}

.burger {
  display: none;
  background: none;
  border: 2px solid var(--blue);
  color: var(--blue);
  border-radius: 12px;
  width: 44px;
  height: 44px;
  font-size: 1.3rem;
  cursor: pointer;
}

/* ===== Desktop ===== */
@media (min-width: 901px) {
  .links.has-pill a {
    position: relative;
    z-index: 1;
  }
  .links.has-pill a.on {
    background: transparent;
    color: #fff;
  }
  /* Sliding pill: 0,45 dtk, kurva elastic (overshoot 1,2) */
  .links.has-pill.ready .pillbg {
    transition:
      transform 0.45s cubic-bezier(0.65, 0, 0.25, 1.2),
      width 0.45s cubic-bezier(0.65, 0, 0.25, 1.2),
      opacity 0.3s;
  }
  /* Nav link lift on hover */
  .links a:not(.on):hover {
    transform: translateY(-2px);
  }
}

/* ===== Mobile & Tablet ===== */
@media (max-width: 900px) {
  .burger {
    display: block;
  }
  nav .btn {
    display: none;
  }
  .pillbg {
    display: none;
  }
  /* Dropdown menu mobile: fade + slide + scale dari kanan atas, 0,25 dtk */
  .links {
    position: absolute;
    left: 5vw;
    right: 5vw;
    top: 100%;
    flex-direction: column;
    background: var(--card);
    padding: 10px;
    border-radius: 20px;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
    display: flex;
    opacity: 0;
    visibility: hidden;
    transform: translateY(-10px) scale(0.97);
    transform-origin: top right;
    transition:
      opacity 0.25s,
      transform 0.25s,
      visibility 0.25s;
  }
  .links.open {
    opacity: 1;
    visibility: visible;
    transform: none;
  }
}

/* Efek halaman: Reduced motion */
@media (prefers-reduced-motion: reduce) {
  nav,
  nav .brand,
  .prog,
  .links,
  .pillbg {
    transition: none !important;
  }
}
</style>