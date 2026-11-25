<script setup lang="ts">
import { Download, Smartphone, Tablet } from 'lucide-vue-next'

// Alamat diisi saat build dari variabel Railway; tombol yang alamatnya kosong tidak ditampilkan.
const apkUrl = import.meta.env.VITE_APK_URL?.trim() ?? ''
const pwaUrl = import.meta.env.VITE_PWA_URL?.trim() ?? ''

const download = {
  title: 'Aplikasi',
  highlight: 'IwaGeprek',
  subtitle: 'Khusus untuk tim IwaGeprek: aplikasi kasir di tablet dan aplikasi karyawan di ponsel.',
  apkLabel: 'Unduh untuk Tablet',
  apkNote: 'Android, berkas APK',
  pwaLabel: 'Buka Aplikasi Karyawan',
  pwaNote: 'Android dan iPhone, lewat peramban',
}
</script>

<template>
  <section v-if="apkUrl || pwaUrl" id="unduh" class="dl">
    <div class="wrap dl-inner">
      <h2 class="dl-title">
        <span class="b">{{ download.title }}</span>
        <span class="r">{{ download.highlight }}</span>
      </h2>
      <p class="dl-sub">{{ download.subtitle }}</p>
      <div class="dl-btns">
        <a v-if="apkUrl" class="btn" :href="apkUrl" download>
          <Tablet class="ic" aria-hidden="true" />
          <span class="dl-text"><b>{{ download.apkLabel }}</b><small>{{ download.apkNote }}</small></span>
          <Download class="ic" aria-hidden="true" />
        </a>
        <a v-if="pwaUrl" class="btn o" :href="pwaUrl" target="_blank" rel="noopener">
          <Smartphone class="ic" aria-hidden="true" />
          <span class="dl-text"><b>{{ download.pwaLabel }}</b><small>{{ download.pwaNote }}</small></span>
        </a>
      </div>
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
.dl-btns {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  justify-content: center;
}
.dl-btns .btn {
  padding: 12px 24px;
  border-radius: 999px;
  gap: 12px;
}
.dl-text {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  line-height: 1.25;
}
.dl-text small {
  font-weight: 500;
  opacity: 0.85;
}
@media (max-width: 480px) {
  .dl {
    padding: 48px 0;
  }
  .dl-btns .btn {
    flex: 1 1 100%;
    justify-content: center;
  }
}
</style>
