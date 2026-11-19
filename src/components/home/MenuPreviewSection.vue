<script setup lang="ts">
import { ArrowRight } from 'lucide-vue-next'
import AnchorLink from '@/components/AnchorLink.vue'
import MenuCard from '@/components/MenuCard.vue'
import { menuIntro, menuItems, PREVIEW_COUNT } from '@/data/menu'

const previewItems = menuItems.slice(0, PREVIEW_COUNT)
</script>

<template>
  <section id="menu-preview" class="menu menu-preview">
    <div class="wrap">
      <div class="menu-head">
        <h2>{{ menuIntro.title }}</h2>
        <p>{{ menuIntro.subtitle }}</p>
      </div>
      <div class="grid">
        <MenuCard v-for="item in previewItems" :key="item.id" :item="item" />
      </div>
      <div class="more">
        <AnchorLink class="btn" to="/menu">
          Lihat Menu Selengkapnya <ArrowRight class="ic" aria-hidden="true" />
        </AnchorLink>
      </div>
    </div>
  </section>
</template>

<style scoped>
.menu-preview {
  position: relative;
  z-index: 1;
  margin-top: -2px;
}
.more {
  text-align: center;
  margin-top: 48px;
}
@media (max-width: 900px) {
  .more {
    margin-top: 28px;
  }
}

.menu {
  background: var(--deep);
  color: var(--cream);
  padding: 110px 0;
  line-height: 1.6;
  font-size: 17px;
}
.mpage {
  min-height: 70vh;
  padding: 60px 0 120px;
}
@media (max-width: 900px) {
  .menu {
    padding: 56px 0;
  }
  .mpage {
    padding: 40px 0 80px;
  }
}

.menu-head {
  display: flex;
  justify-content: space-between;
  align-items: end;
  gap: 30px;
  flex-wrap: wrap;
  margin-bottom: 48px;
}
.menu-head h2 {
  font-size: clamp(2rem, 4.6vw, 3.4rem);
  font-weight: 800;
  line-height: 1.1;
  letter-spacing: -0.01em;
}
.menu-head p {
  max-width: 26em;
  color: var(--color-brand-powder);
}
@media (max-width: 900px) {
  .menu-head {
    margin-bottom: 22px;
    gap: 8px;
  }
  .menu-head h2 {
    font-size: 1.9rem;
    overflow-wrap: anywhere;
  }
  .menu-head p {
    font-size: 0.92rem;
  }
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(290px, 1fr));
  gap: 26px;
}
@media (max-width: 900px) {
  .grid {
    grid-template-columns: minmax(0, 1fr);
    gap: 12px;
  }
}
</style>