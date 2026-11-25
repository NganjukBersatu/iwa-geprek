<script setup lang="ts">
import { ArrowRight, Download } from 'lucide-vue-next'

// Alamat halaman Unduhan diisi saat build dari variabel Railway; bagian ini tidak tampil bila kosong.
const downloadPageUrl = import.meta.env.VITE_DOWNLOAD_PAGE_URL?.trim() ?? ''

const download = {
  title: 'Aplikasi',
  highlight: 'IwaGeprek',
  subtitle: 'Khusus untuk tim IwaGeprek: aplikasi kasir di tablet dan aplikasi karyawan di ponsel.',
  label: 'Ke Halaman Unduhan',
}
</script>

<template>
  <section v-if="downloadPageUrl" id="unduh" class="dl">
    <div class="wrap">
      <h2 class="dl-title">
        <span class="b">{{ download.title }}</span>
        <span class="r">{{ download.highlight }}</span>
      </h2>
      <p class="dl-sub">{{ download.subtitle }}</p>
      <a class="btn" :href="downloadPageUrl" target="_blank" rel="noopener">
        <Download class="ic" aria-hidden="true" /> {{ download.label }} <ArrowRight class="ic" aria-hidden="true" />
      </a>
    </div>
  </section>
</template>

<style scoped>
.dl {
  background: var(--deco);
  padding: 64px 0;
  text-align: center;
}
.dl-title {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0 0.3em;
  font-size: clamp(1.8rem, 3.6vw, 2.8rem);
  font-weight: 800;
  line-height: 1.15;
}
.dl-title .b {
  color: var(--blue);
}
.dl-title .r {
  color: var(--red);
  font-style: italic;
}
.dl-sub {
  color: var(--blue);
  font-weight: 600;
  margin: 12px auto 28px;
  max-width: 560px;
}
.dl .btn {
  padding: 12px 28px;
  border-radius: 999px;
  gap: 10px;
}
@media (max-width: 480px) {
  .dl {
    padding: 48px 0;
  }
}
</style>
