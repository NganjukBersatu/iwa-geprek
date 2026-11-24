import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'
import MenuView from '@/views/MenuView.vue'

/** Offset agar section tidak tertutup navbar sticky (sama dengan scroll-padding-top di base.css). */
const SCROLL_OFFSET = 84

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: HomeView },
    { path: '/menu', name: 'menu', component: MenuView },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
  scrollBehavior(to, _from, savedPosition) {
    if (savedPosition) return savedPosition
    if (to.hash) return { el: to.hash, top: SCROLL_OFFSET }
    return { top: 0, behavior: 'instant' }
  },
})

export default router