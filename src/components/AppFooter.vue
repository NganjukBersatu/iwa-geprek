<script setup lang="ts">
import { Clock, Mail, MapPin, MessageCircle, Instagram } from 'lucide-vue-next'
import AnchorLink from '@/components/AnchorLink.vue'
import logo from '@/assets/images/logo-iwageprek-hd.png'
import { business, navLinks, socialLinks } from '@/data/site'
</script>

<template>
  <footer class="site">
    <div class="wrap fgrid">
      <div class="fb1">
        <AnchorLink class="brand fbrand" to="/#beranda">
          <span class="mark"><img :src="logo" alt="Logo IWAGEPREK" /></span>
          <span class="word">
            <b>IWA<i>GEPREK</i></b>
            <small>{{ business.tagline }}</small>
          </span>
        </AnchorLink>
        <p>{{ business.footerText }}</p>
        <!-- Efek hover: color fill pada ikon sosial media -->
        <div class="soc">
          <a
            v-for="social in socialLinks"
            :key="social.label"
            :href="social.url"
            target="_blank"
            rel="noopener"
            :aria-label="social.label"
          >
            <component :is="social.icon" aria-hidden="true" />
          </a>
        </div>
      </div>

      <div>
        <h4>Navigasi</h4>
        <ul>
          <!-- Efek hover: slide-right nudge -->
          <li v-for="link in navLinks" :key="link.key">
            <AnchorLink :to="link.to">{{ link.label }}</AnchorLink>
          </li>
        </ul>
      </div>

      <div>
        <h4>Hubungi Kami</h4>
        <ul class="fc">
          <li>
            <MapPin aria-hidden="true" />
            <span>
              <a :href="business.mapsUrl" target="_blank" rel="noopener">{{ business.address }}</a>
            </span>
          </li>
          <li>
            <MessageCircle aria-hidden="true" />
            <span>
              <a :href="business.whatsappUrl" target="_blank" rel="noopener">{{ business.phoneDisplay }}</a>
            </span>
          </li>
          <li>
            <Mail aria-hidden="true" />
            <span>
              <a :href="`mailto:${business.email}`">{{ business.email }}</a>
            </span>
          </li>
          <li>
            <Instagram aria-hidden="true" />
            <span>
              <a :href="business.instagramUrl" target="_blank" rel="noopener">{{ business.instagramHandle }}</a>
            </span>
          </li>
          <li>
            <Clock aria-hidden="true" />
            <span>{{ business.hours }}</span>
          </li>
        </ul>
      </div>
    </div>
    <div class="wrap fcopy">{{ business.copyright }}</div>
  </footer>
</template>

<style scoped>
footer.site {
  position: relative;
  z-index: 2;
  background: var(--deep);
  color: var(--color-brand-frost);
  padding: 64px 0 0;
  line-height: 1.6;
  font-size: 16px;
  border-top: 5px solid transparent;
  border-image: linear-gradient(90deg, #cc0b14, #0898e8) 1;
}
.fgrid {
  display: grid;
  grid-template-columns: 1.4fr 0.8fr 1.2fr;
  gap: 44px;
}
h4 {
  color: #fff;
  font-weight: 700;
  font-size: 1.05rem;
  margin-bottom: 18px;
  padding-bottom: 10px;
  position: relative;
}
h4::after {
  content: '';
  position: absolute;
  left: 0;
  bottom: 0;
  width: 34px;
  height: 3px;
  border-radius: 3px;
  background: var(--red);
}
ul {
  list-style: none;
  padding: 0;
  display: grid;
  gap: 10px;
}
a {
  color: inherit;
  text-decoration: none;
  transition: 0.2s;
}
ul a:hover {
  color: #fff;
  padding-left: 4px;
}
.fc li {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}
.fc svg {
  width: 18px;
  height: 18px;
  flex: none;
  margin-top: 4px;
  stroke: var(--sky);
}
.fb1 p {
  margin: 16px 0 20px;
  max-width: 30em;
}
.soc {
  display: flex;
  gap: 10px;
}
.soc a {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  display: grid;
  place-items: center;
  color: #fff;
}
.soc a:hover {
  background: var(--red);
}
.soc svg {
  width: 20px;
  height: 20px;
}
.fcopy {
  margin-top: 46px;
  padding: 20px 24px 26px;
  border-top: 1px solid rgba(255, 255, 255, 0.14);
  text-align: center;
  font-size: 0.88rem;
  color: var(--color-brand-haze);
}

/* Logo versi footer */
.fbrand :deep(.word b) {
  color: #fff;
}
.fbrand :deep(.word b i) {
  color: var(--color-brand-salmon);
}
.fbrand :deep(.word small) {
  color: var(--color-brand-skylight);
}
.fbrand :deep(.word small::before) {
  background: var(--color-brand-skylight);
}

@media (max-width: 900px) {
  .fgrid {
    grid-template-columns: 1fr 1fr;
  }
  .fb1 {
    grid-column: 1/-1;
  }
}
@media (max-width: 520px) {
  .fgrid {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>