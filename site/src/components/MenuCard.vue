<script setup lang="ts">
import { computed, ref } from 'vue'
import { ArrowRight, ChevronDown, Flame } from 'lucide-vue-next'
import { formatRupiah, type MenuItem } from '@/data/menu'

const props = defineProps<{ item: MenuItem }>()

const expanded = ref(false)

/** Harga terendah dari semua varian (untuk menu tambahan: harga tunggalnya). */
const startPrice = computed(() =>
  props.item.variants
    ? Math.min(...props.item.variants.flatMap((v) => v.options.map((o) => o.price)))
    : (props.item.price ?? 0),
)
</script>

<template>
  <!-- Efek hover: lift + shadow expand; foto zoom -->
  <article class="item" :class="{ simple: !item.variants }">
    <div v-if="item.image" class="thumb">
      <img :src="item.image" :alt="item.imageAlt" width="512" height="640" loading="lazy" />
      <span v-if="item.variants" class="tag">
        <Flame class="ic" aria-hidden="true" />{{ item.category }}
      </span>
    </div>

    <div class="body">
      <h3>{{ item.name }}</h3>

      <!-- Menu utama: daftar varian, tampil saat diklik -->
      <template v-if="item.variants">
        <div v-if="expanded" :id="`variants-${item.id}`" class="variants">
          <div v-for="variant in item.variants" :key="variant.name" class="variant">
            <span class="vtag" :class="variant.tone">{{ variant.name }}</span>
            <ul class="plist">
              <li v-for="opt in variant.options" :key="opt.label">
                <span>{{ opt.label }}</span>
                <strong :class="variant.tone">{{ formatRupiah(opt.price) }}</strong>
              </li>
            </ul>
          </div>
        </div>

        <button
          type="button"
          class="more"
          :aria-expanded="expanded"
          :aria-controls="`variants-${item.id}`"
          @click="expanded = !expanded"
        >
          {{ expanded ? 'Sembunyikan' : 'Lihat selengkapnya' }}
          <ChevronDown class="chev" :class="{ open: expanded }" aria-hidden="true" />
        </button>
      </template>

      <!-- Menu tambahan: ruang kosong seukuran tombol di atas, supaya tinggi kartu sama -->
      <div v-else class="spacer" aria-hidden="true"></div>

      <div class="foot">
        <span class="iprice">
          <small v-if="item.variants">Mulai</small>
          <span>{{ formatRupiah(startPrice) }}</span>
        </span>
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
  aspect-ratio: 16/10;
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
  margin-bottom: 12px;
  font-weight: 800;
  line-height: 1.2;
  letter-spacing: -0.01em;
}

/* Varian harga */
.variants {
  margin-bottom: 4px;
}
.variant {
  margin-bottom: 14px;
}
.vtag {
  display: inline-block;
  font-size: 0.72rem;
  font-weight: 800;
  font-style: italic;
  color: #fff;
  padding: 4px 12px;
  border-radius: 99px;
  margin-bottom: 8px;
}
.vtag.geprek {
  background: var(--blue);
}
.vtag.api {
  background: var(--red);
}
.plist {
  list-style: none;
  margin: 0;
  padding: 0;
}
.plist li {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  font-size: 0.9rem;
  padding: 2px 0;
}
.plist strong {
  font-weight: 800;
  white-space: nowrap;
}
.plist strong.geprek {
  color: var(--blue);
}
.plist strong.api {
  color: var(--red);
}

/* Tombol "Lihat selengkapnya" (tinggi 24px + jarak 14px = 38px) */
.more {
  display: inline-flex;
  align-items: center;
  align-self: flex-start;
  gap: 6px;
  height: 24px;
  margin-bottom: 14px;
  padding: 0;
  background: none;
  border: 0;
  color: var(--blue);
  font: 600 0.88rem var(--font-sans);
  cursor: pointer;
  transition: color 0.2s;
}
.more:hover {
  color: var(--red);
}
.chev {
  width: 16px;
  height: 16px;
  flex: none;
  transition: transform 0.25s;
}
.chev.open {
  transform: rotate(180deg);
}

/* Ruang pengganti tombol di kartu tambahan (tinggi harus sama dengan .more) */
.spacer {
  height: 38px;
  flex: none;
}

.foot {
  margin-top: auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  min-height: 44px; /* sama dengan tinggi tombol Pesan */
  padding-top: 14px;
  box-sizing: content-box;
  border-top: 2px dashed var(--deco);
}
.iprice {
  display: inline-flex;
  align-items: baseline;
  gap: 6px;
  color: var(--red);
  font-weight: 800;
  font-size: 1.2rem;
}
.iprice small {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--muted);
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
    border-radius: 20px;
    padding: 10px;
    box-shadow: 0 10px 24px rgba(0, 0, 0, 0.22);
  }
  .item:hover {
    transform: none;
  }
  .thumb {
    aspect-ratio: 16/9;
    border-radius: 15px;
  }
  .body {
    padding: 14px 6px 4px;
    min-width: 0;
  }
  .item h3 {
    font-size: 1.05rem;
    margin-bottom: 8px;
  }
  .plist li {
    font-size: 0.85rem;
  }
  .foot {
    min-height: 0;
    padding-top: 10px;
    border-top-width: 1.5px;
  }
  .iprice {
    font-size: 0.95rem;
  }
  .order {
    padding: 7px 13px;
    font-size: 0.8rem;
  }

  /* Kartu tambahan: baris dengan foto kecil di kiri */
  .item.simple {
    flex-direction: row;
    align-items: center;
    gap: 12px;
  }
  .item.simple .thumb {
    width: 90px;
    aspect-ratio: 1;
    border-radius: 14px;
  }
  .item.simple .body {
    padding: 0;
    flex: 1;
  }
  .item.simple .spacer {
    display: none;
  }
}
</style>