<script setup lang="ts">
import { computed, ref } from 'vue'
import { ArrowLeft } from 'lucide-vue-next'
import AnchorLink from '@/components/AnchorLink.vue'
import MenuCard from '@/components/MenuCard.vue'
import { menuFilters, menuIntro, menuItems, type FilterKey } from '@/data/menu'

const activeFilter = ref<FilterKey>('all')

const visibleItems = computed(() =>
  activeFilter.value === 'all'
    ? menuItems
    : menuItems.filter((item) => item.category === activeFilter.value),
)
</script>

<template>
  <main id="menu-page">
    <section class="menu mpage">
      <div class="wrap">
        <AnchorLink class="back" to="/#beranda">
          <ArrowLeft class="ic" aria-hidden="true" /> Kembali ke Beranda
        </AnchorLink>

        <div class="menu-head">
          <h2>{{ menuIntro.fullTitle }}</h2>
          <p>{{ menuIntro.subtitle }}</p>
        </div>

        <div class="filters" role="group" aria-label="Filter kategori menu">
          <!-- Efek hover: border highlight -->
          <button
            v-for="filter in menuFilters"
            :key="filter.key"
            type="button"
            class="fchip"
            :class="{ on: activeFilter === filter.key }"
            :aria-pressed="activeFilter === filter.key"
            @click="activeFilter = filter.key"
          >
            {{ filter.label }}
          </button>
        </div>

        <div class="grid">
          <MenuCard v-for="item in visibleItems" :key="item.id" :item="item" />
        </div>
      </div>
    </section>
  </main>
</template>

<style scoped>
.back {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--color-brand-powder);
  text-decoration: none;
  font-weight: 600;
  margin-bottom: 26px;
}
.back:hover {
  color: #fff;
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

.filters {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin: 0 0 34px;
}
.fchip {
  border: 2px solid rgba(255, 255, 255, 0.35);
  background: transparent;
  color: #fff;
  font: 600 0.92rem var(--font-sans);
  padding: 9px 22px;
  border-radius: 99px;
  cursor: pointer;
  transition: 0.2s;
}
.fchip:hover {
  border-color: #fff;
}
.fchip.on {
  background: var(--red);
  border-color: var(--red);
}
@media (max-width: 900px) {
  .filters {
    margin-bottom: 22px;
    gap: 8px;
  }
  .fchip {
    padding: 7px 16px;
    font-size: 0.85rem;
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