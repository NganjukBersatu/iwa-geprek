<script setup lang="ts">
import { ArrowRight, Flame } from 'lucide-vue-next'
import AnchorLink from '@/components/AnchorLink.vue'
import { formatRupiah, type MenuItem } from '@/data/menu'

defineProps<{ item: MenuItem }>()
</script>

<template>
  <!-- Efek hover: lift + shadow expand; foto zoom -->
  <article class="item">
    <div class="thumb">
      <img :src="item.image" :alt="item.imageAlt" width="512" height="640" loading="lazy" />
      <span class="tag"><Flame class="ic" aria-hidden="true" />{{ item.category }}</span>
    </div>
    <div class="body">
      <h3>{{ item.name }}</h3>
      <p>{{ item.description }}</p>
      <div class="foot">
        <span class="iprice">{{ formatRupiah(item.price) }}</span>
        <!-- Efek hover: gap expand / arrow slide -->
        <AnchorLink class="order" to="/#kontak">
          Pesan <ArrowRight class="ic" aria-hidden="true" />
        </AnchorLink>
      </div>
    </div>
  </article>
</template>

<style scoped>
.item {
  position: relative;
  border-radius: 30px;
  overflow: hidden;
  background: #fdfdfd;
  color: var(--blue);
  padding: 12px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 22px 44px rgba(0, 0, 0, 0.28);
  transition:
    transform 0.35s,
    box-shadow 0.35s;
}
.item:hover {
  transform: translateY(-8px);
  box-shadow: 0 30px 56px rgba(0, 0, 0, 0.36);
}
.thumb {
  position: relative;
  border-radius: 22px;
  overflow: hidden;
  aspect-ratio: 4/3;
  flex: none;
}
.thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.6s;
}
/* Efek hover: image zoom (scale-up) */
.item:hover .thumb img {
  transform: scale(1.08);
}
.tag {
  position: absolute;
  left: 12px;
  top: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(253, 253, 253, 0.94);
  color: var(--red);
  font-size: 0.75rem;
  font-weight: 700;
  padding: 6px 12px;
  border-radius: 99px;
  box-shadow: 0 6px 14px rgba(0, 0, 0, 0.18);
}
.body {
  display: flex;
  flex-direction: column;
  flex: 1;
  padding: 18px 10px 8px;
}
.item h3 {
  font-size: 1.2rem;
  color: var(--blue);
  margin-bottom: 8px;
  font-weight: 800;
  line-height: 1.2;
  letter-spacing: -0.01em;
}
.item p {
  color: var(--muted);
  font-size: 0.92rem;
  margin-bottom: 18px;
}
.foot {
  margin-top: auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding-top: 14px;
  border-top: 2px dashed var(--deco);
}
.iprice {
  display: inline-block;
  color: var(--red);
  font-weight: 800;
  font-size: 1.2rem;
}
.order {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: var(--red);
  color: #fff;
  text-decoration: none;
  font-weight: 600;
  font-size: 0.88rem;
  padding: 10px 18px;
  border-radius: 99px;
  transition: 0.2s;
}
.order:hover {
  background: var(--blue);
  gap: 12px;
}

@media (max-width: 900px) {
  .item {
    flex-direction: row;
    align-items: center;
    gap: 12px;
    padding: 10px;
    border-radius: 20px;
    box-shadow: 0 10px 24px rgba(0, 0, 0, 0.22);
  }
  .item:hover {
    transform: none;
  }
  .thumb {
    width: 100px;
    height: 100px;
    aspect-ratio: 1;
    border-radius: 15px;
  }
  .tag {
    display: none;
  }
  .body {
    padding: 0;
    min-width: 0;
  }
  .item h3 {
    font-size: 1rem;
    margin-bottom: 3px;
  }
  .item p {
    font-size: 0.8rem;
    line-height: 1.4;
    margin-bottom: 8px;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
  .foot {
    padding-top: 8px;
    gap: 8px;
    border-top-width: 1.5px;
  }
  .iprice {
    font-size: 0.95rem;
  }
  .order {
    padding: 7px 13px;
    font-size: 0.8rem;
  }
}
</style>