<script setup lang="ts">
import { ArrowRight, Clock, Mail, MapPin, Phone } from 'lucide-vue-next'
import logo from '@/assets/images/logo-iwageprek.png'
import { business } from '@/data/site'

// ===== Data Kontak =====
const contactIntro = {
  eyebrow: 'HUBUNGI KAMI',
  titleBlue: 'Kontak &',
  titleRed: 'Lokasi',
  subtitle: 'Kami siap melayani Anda dengan sepenuh hati. Jangan ragu untuk menghubungi kami!',
  mapsButton: 'Lihat di Google Maps',
  mapLabelLink: 'Lihat peta lebih besar',
}

const contactItems = [
  {
    id: 'telepon',
    label: 'Telepon',
    value: business.phoneDisplay,
    href: business.phoneHref,
    icon: Phone,
    tone: 'red',
  },
  {
    id: 'email',
    label: 'Email',
    value: business.email,
    href: `mailto:${business.email}`,
    icon: Mail,
    tone: 'blue',
  },
  { id: 'alamat', label: 'Alamat', value: business.address, icon: MapPin, tone: 'blue' },
  { id: 'jam', label: 'Jam Operasional', value: business.hours, icon: Clock, tone: 'red' },
]
</script>

<template>
  <section id="kontak" class="contact">
    <img class="cwm" :src="logo" alt="" />
    <!-- bob: tetesan air -->
    <svg class="drop d1 animate-bob motion-reduce:animate-none" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2C12 2 4 11 4 16a8 8 0 0 0 16 0c0-5-8-14-8-14Z" /></svg>
    <svg class="drop d2 animate-bob motion-reduce:animate-none" viewBox="0 0 24 24" aria-hidden="true" style="animation-delay: -2s"><path d="M12 2C12 2 4 11 4 16a8 8 0 0 0 16 0c0-5-8-14-8-14Z" /></svg>
    <svg class="drop d3 animate-bob motion-reduce:animate-none" viewBox="0 0 24 24" aria-hidden="true" style="animation-delay: -3s"><path d="M12 2C12 2 4 11 4 16a8 8 0 0 0 16 0c0-5-8-14-8-14Z" /></svg>

    <div class="wrap cgrid">
      <div class="cl">
        <div class="ceye">
          <span>{{ contactIntro.eyebrow }}</span>
        </div>
        <h2 class="ctitle">
          <span class="b">{{ contactIntro.titleBlue }}</span>
          <span class="r">{{ contactIntro.titleRed }}</span>
        </h2>
        <p class="csub">{{ contactIntro.subtitle }}</p>

        <div class="infos">
          <template v-for="item in contactItems" :key="item.id">
            <!-- Efek hover: lift + shadow expand (khusus yang berupa link) -->
            <a v-if="item.href" class="info" :href="item.href">
              <span class="ico" :class="item.tone"><component :is="item.icon" aria-hidden="true" /></span>
              <span class="txt"
                ><b>{{ item.label }}</b
                >{{ item.value }}</span
              >
            </a>
            <div v-else class="info">
              <span class="ico" :class="item.tone"><component :is="item.icon" aria-hidden="true" /></span>
              <span class="txt"
                ><b>{{ item.label }}</b
                >{{ item.value }}</span
              >
            </div>
          </template>
        </div>

        <a class="btn" :href="business.mapsUrl" target="_blank" rel="noopener">
          <MapPin class="ic" aria-hidden="true" /> {{ contactIntro.mapsButton }}
          <ArrowRight class="ic" aria-hidden="true" />
        </a>
      </div>

      <div id="lokasi" class="mapcard">
        <svg class="mapsvg" viewBox="0 0 640 460" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
          <rect width="640" height="460" fill="#EDEFF3" />
          <rect x="430" y="0" width="210" height="460" fill="#F7EEDC" opacity=".7" />
          <rect x="40" y="330" width="150" height="90" rx="10" fill="#D5EAD2" />
          <rect x="330" y="30" width="90" height="70" rx="8" fill="#DCEFD9" />
          <path d="M-10 120 L650 330" stroke="#fff" stroke-width="22" />
          <path d="M270 -10 L420 470" stroke="#fff" stroke-width="18" />
          <path d="M-10 250 L650 70" stroke="#fff" stroke-width="9" />
          <path d="M110 -10 L250 470" stroke="#fff" stroke-width="7" />
          <path d="M520 -10 L560 470" stroke="#fff" stroke-width="7" />
          <path d="M-10 400 L650 440" stroke="#fff" stroke-width="7" />
          <path d="M-10 60 L650 20" stroke="#fff" stroke-width="6" />
          <path
            d="M60 -10 C120 120 90 250 190 470"
            fill="none"
            stroke="#BFE0F5"
            stroke-width="8"
            stroke-linecap="round"
          />
          <text x="400" y="190" font-size="17" fill="#6b7280" font-family="Poppins,sans-serif">Kertosono</text>
        </svg>
        <a
          class="mapcover"
          :href="business.mapsUrl"
          target="_blank"
          rel="noopener"
          aria-label="Buka lokasi IWAGEPREK di Google Maps"
        ></a>
        <div class="maplabel">
          <b>{{ business.name }}</b>
          <span>{{ business.address }}</span>
          <a :href="business.mapsUrl" target="_blank" rel="noopener">{{ contactIntro.mapLabelLink }}</a>
        </div>
        <div class="pinwrap">
          <!-- Pl: bayangan pulse; Pin: ikon memantul -->
          <span class="pulse animate-pl motion-reduce:animate-none"></span>
          <svg class="pinic animate-pin motion-reduce:animate-none" viewBox="0 0 40 52" aria-hidden="true">
            <path
              d="M20 0C9 0 0 9 0 20c0 15 20 32 20 32s20-17 20-32C40 9 31 0 20 0Z"
              fill="#CC0B14"
            />
            <circle cx="20" cy="20" r="8" fill="#7a0309" />
          </svg>
          <em>{{ business.name }}</em>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.contact {
  position: relative;
  overflow: hidden;
  background: #fdfdfd;
  padding: 100px 0 110px;
  line-height: 1.6;
  font-size: 17px;
}
.contact::before {
  content: '';
  position: absolute;
  left: -12%;
  top: -10%;
  width: 50%;
  aspect-ratio: 1;
  border-radius: 50%;
  background: var(--deco);
  opacity: 0.55;
}
.cwm {
  position: absolute;
  right: -3%;
  top: -6%;
  width: min(40vw, 520px);
  opacity: 0.14;
  transform: rotate(-8deg);
  pointer-events: none;
}
.drop {
  width: 44px;
  opacity: 0.85;
}
.d1 {
  left: 44%;
  top: 70px;
  transform: rotate(30deg);
}
.d2 {
  left: 47%;
  top: 120px;
  width: 28px;
}
.d3 {
  left: 38%;
  bottom: 150px;
  width: 34px;
}
.cgrid {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: 1.05fr 1fr;
  gap: 48px;
  align-items: center;
}
.ceye {
  display: flex;
  align-items: center;
  gap: 14px;
  color: var(--red);
  font-weight: 600;
  letter-spacing: 0.3em;
  font-size: 0.8rem;
  margin-bottom: 10px;
}
.ceye::before,
.ceye::after {
  content: '';
  width: 60px;
  height: 2px;
  background: var(--red);
}
.ctitle {
  font-size: clamp(3rem, 6.4vw, 5.4rem);
  font-style: italic;
  font-weight: 800;
  line-height: 0.98;
  letter-spacing: -0.02em;
}
.ctitle .b {
  display: block;
  color: var(--blue);
}
.ctitle .r {
  display: block;
  color: var(--red);
}
.csub {
  color: var(--muted);
  margin: 18px 0 26px;
  max-width: 32em;
}
.infos {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  margin-bottom: 28px;
}
.info {
  display: flex;
  align-items: center;
  gap: 14px;
  background: linear-gradient(180deg, #fff, var(--color-brand-mist));
  border: 2px solid #fff;
  border-radius: 22px;
  padding: 14px 16px;
  text-decoration: none;
  color: var(--muted);
  font-size: 0.95rem;
  box-shadow: 0 10px 26px rgba(1, 93, 247, 0.1);
  transition: 0.25s;
}
a.info:hover {
  transform: translateY(-3px);
  box-shadow: 0 16px 30px rgba(1, 93, 247, 0.18);
}
.ico {
  flex: none;
  width: 50px;
  height: 50px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  color: #fff;
}
.ico.red {
  background: var(--red);
}
.ico.blue {
  background: var(--blue);
}
.ico svg {
  width: 24px;
  height: 24px;
}
.txt {
  line-height: 1.35;
  word-break: break-word;
}
.txt b {
  display: block;
  color: var(--blue);
  font-weight: 700;
  line-height: 1.3;
}

/* ----- Peta ----- */
.mapcard {
  position: relative;
  aspect-ratio: 1.18;
  border-radius: 36px;
  overflow: hidden;
  border: 10px solid #fff;
  box-shadow:
    0 0 0 3px rgba(8, 152, 232, 0.25),
    0 30px 60px rgba(1, 93, 247, 0.25);
  background: #edeff3;
}
.mapsvg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}
.mapcover {
  position: absolute;
  inset: 0;
  z-index: 1;
  cursor: pointer;
}
.maplabel {
  position: absolute;
  left: 16px;
  top: 16px;
  z-index: 2;
  background: #fff;
  border-radius: 16px;
  padding: 12px 18px;
  box-shadow: 0 8px 22px rgba(0, 0, 0, 0.16);
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 0.88rem;
  color: #444;
}
.maplabel b {
  color: #111;
  font-size: 0.98rem;
}
.maplabel a {
  color: #1a56d6;
  font-size: 0.82rem;
}
.pinwrap {
  position: absolute;
  left: 50%;
  top: 56%;
  transform: translate(-50%, -100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  pointer-events: none;
  z-index: 1;
}
.pinic {
  width: 38px;
  filter: drop-shadow(0 6px 6px rgba(0, 0, 0, 0.3));
}
.pinwrap em {
  position: absolute;
  left: 46px;
  top: 6px;
  font-style: normal;
  font-weight: 700;
  color: var(--red);
  font-size: 0.9rem;
  white-space: nowrap;
  text-shadow:
    0 0 4px #fff,
    0 0 4px #fff;
}
.pulse {
  position: absolute;
  bottom: -8px;
  width: 34px;
  height: 12px;
  border-radius: 50%;
  background: rgba(204, 11, 20, 0.35);
}

@media (max-width: 900px) {
  .contact {
    padding: 76px 0 110px;
  }
  .d1,
  .d2 {
    display: none;
  }
  .cgrid {
    grid-template-columns: minmax(0, 1fr);
  }
  .cgrid > * {
    min-width: 0;
  }
  .ctitle {
    overflow-wrap: anywhere;
  }
  .mapcard {
    aspect-ratio: 1.1;
    border-width: 6px;
    border-radius: 28px;
  }
  .maplabel {
    left: 8px;
    top: 8px;
    padding: 6px 10px;
    border-radius: 11px;
    gap: 0;
    font-size: 0.64rem;
    line-height: 1.3;
    max-width: 62%;
  }
  .maplabel b {
    font-size: 0.74rem;
  }
  .maplabel a {
    font-size: 0.62rem;
  }
  .pinwrap {
    top: 70%;
    left: 56%;
  }
  .pinic {
    width: 30px;
  }
  .pinwrap em {
    left: 36px;
    top: 3px;
    font-size: 0.78rem;
  }
}
@media (max-width: 520px) {
  .infos {
    grid-template-columns: minmax(0, 1fr);
  }
  .ctitle {
    font-size: 3rem;
  }
}
</style>