<script setup lang="ts">
import { Fish, Flame, MapPin, Star, Zap } from 'lucide-vue-next'
import AnchorLink from '@/components/AnchorLink.vue'
import logo from '@/assets/images/logo.jpeg'
import heroPhoto from '@/assets/images/hero.jpeg'

// ===== Data Hero =====
const hero = {
  eyebrow: 'LEZAT • SEGAR • BERGIZI',
  titleBlue: 'Nikmatnya',
  titleRed: 'Ikan Geprek',
  subtitle: 'Rasakan kelezatan ikan goreng dengan sambal geprek khas Iwageprek yang menggugah selera.',
  photo: heroPhoto,
  photoAlt: 'Ikan geprek dengan nasi, lalapan, dan sambal',
  ratingValue: '4,9',
  ratingLabel: 'Pelanggan puas',
  spiceTitle: 'Pedas Gila',
  spiceLabel: 'Level sesuai selera',
  priceCaption: 'MULAI',
  priceValue: 'Rp15rb',
}

const heroChips = [
  { label: 'Ikan Segar', icon: Fish },
  { label: 'Sambal Nampol', icon: Flame },
  { label: 'Cepat Saji', icon: Zap },
]
</script>

<template>
  <section id="beranda" class="hero">
    <!-- Gelombang dekoratif (merah → biru → putih) -->
    <svg class="hwave" viewBox="0 0 1440 180" preserveAspectRatio="none" aria-hidden="true">
      <path d="M520 110C820 70 1200 -4 1440 30V160H520Z" fill="#CC0B14" />
      <path
        d="M0 70C260 22 640 96 960 66C1160 48 1320 34 1440 52V160H0Z"
        fill="#015DF7"
      />
      <path
        d="M0 132C300 104 660 150 980 128C1170 115 1320 112 1440 124V180H0Z"
        fill="#FDFDFD"
      />
    </svg>
    <img class="wm" :src="logo" alt="" />

    <div class="copy">
      <div class="eyebrow">{{ hero.eyebrow }}</div>
      <h1>
        <span class="b">{{ hero.titleBlue }}</span>
        <span class="r">{{ hero.titleRed }}</span>
      </h1>
      <p class="sub">{{ hero.subtitle }}</p>
      <div class="cta">
        <AnchorLink class="btn" to="/#kontak">Pesan Sekarang</AnchorLink>
        <AnchorLink class="btn o" to="/#lokasi">
          <MapPin class="ic" aria-hidden="true" /> Lihat Lokasi
        </AnchorLink>
      </div>
      <div class="chips">
        <span v-for="chip in heroChips" :key="chip.label" class="chip">
          <component :is="chip.icon" class="ic" aria-hidden="true" /> {{ chip.label }}
        </span>
      </div>
    </div>

    <div class="visual">
      <div class="ring-red"></div>
      <!-- Spin: cincin putus-putus -->
      <div class="ring-dash animate-spin-slow motion-reduce:animate-none"></div>
      <!-- Float: foto hero -->
      <div class="photo animate-float motion-reduce:animate-none">
        <img :src="hero.photo" :alt="hero.photoAlt" width="1100" height="733" />
      </div>
      <!-- bob: badge & bulatan harga -->
      <div class="orbit">
        <div
          class="badge b2 animate-bob motion-reduce:animate-none"
          style="animation-duration: 5.4s; animation-delay: -1.6s"
        >
          <Star class="ic" aria-hidden="true" style="fill: #ffc83d; stroke: #ffc83d" />
          {{ hero.ratingValue }}<small>{{ hero.ratingLabel }}</small>
        </div>
        <div class="badge b1 animate-bob motion-reduce:animate-none" style="animation-duration: 4.6s">
          <Flame class="ic" aria-hidden="true" />
          <span>
            {{ hero.spiceTitle }}<small>{{ hero.spiceLabel }}</small>
          </span>
        </div>
        <div
          class="price animate-bob motion-reduce:animate-none"
          style="animation-duration: 5s; animation-delay: -3s"
        >
          <span>
            <small>{{ hero.priceCaption }}</small
            >{{ hero.priceValue }}
          </span>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.hero {
  position: relative;
  z-index: 1;
  overflow: hidden;
  display: grid;
  grid-template-columns: 1.05fr 1fr;
  align-items: center;
  gap: 30px;
  padding: 40px 5vw clamp(260px, 17vw, 360px);
  min-height: calc(100vh - 80px);
  background: #fdfdfd;
}
.hwave {
  position: absolute;
  left: 0;
  bottom: -1px;
  width: 100%;
  height: 170px;
  z-index: 2;
  pointer-events: none;
}
.wm {
  position: absolute;
  right: 4%;
  top: 20px;
  width: 30vw;
  max-width: 420px;
  opacity: 0.16;
  z-index: 0;
  pointer-events: none;
  transform: rotate(-8deg);
}
.copy,
.visual {
  position: relative;
  z-index: 1;
}

.eyebrow {
  display: flex;
  align-items: center;
  gap: 14px;
  color: var(--red);
  font-weight: 500;
  letter-spacing: 0.28em;
  font-size: 0.8rem;
  margin-bottom: 14px;
}
.eyebrow::before {
  content: '';
  width: 70px;
  height: 2px;
  background: var(--red);
}
h1 {
  font-size: clamp(2.8rem, 6.6vw, 5.6rem);
  line-height: 1;
  font-weight: 800;
  font-style: italic;
  letter-spacing: -0.02em;
}
h1 .b {
  color: var(--blue);
  display: block;
}
h1 .r {
  color: var(--red);
  display: block;
}
.sub {
  margin: 22px 0 30px;
  color: var(--muted);
  font-size: 1.15rem;
  line-height: 1.6;
  max-width: 30ch;
}
.cta {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}
.chips {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 34px;
}
.chip {
  background: var(--card);
  border-radius: 16px;
  padding: 10px 16px;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--blue);
  box-shadow: 0 6px 20px rgba(1, 93, 247, 0.12);
  display: flex;
  gap: 8px;
  align-items: center;
}
.chip .ic {
  color: var(--red);
}

/* ----- Visual kanan ----- */
.visual {
  isolation: isolate;
  display: grid;
  place-items: center;
  padding: 20px;
}
.visual::before {
  content: '';
  position: absolute;
  width: 100%;
  aspect-ratio: 1;
  border-radius: 50%;
  background: var(--deco);
  right: -12%;
  top: 50%;
  transform: translateY(-50%);
  z-index: -1;
}
.ring-red {
  position: absolute;
  width: 88%;
  aspect-ratio: 1;
  border-radius: 50%;
  background: radial-gradient(circle at 30% 30%, var(--color-brand-coral), var(--red));
  transform: translate(6%, -2%);
}
.ring-dash {
  position: absolute;
  width: 94%;
  aspect-ratio: 1;
  border-radius: 50%;
  border: 3px dashed var(--sky);
  opacity: 0.6;
}
.photo {
  position: relative;
  width: 88%;
  z-index: 1;
  aspect-ratio: 5/4;
  border-radius: 46% 54% 50% 50%/52% 46% 54% 48%;
  overflow: hidden;
  border: 8px solid #fff;
  box-shadow: 0 30px 60px rgba(1, 93, 247, 0.35);
}
.photo img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transform: scale(1.04);
}
.orbit {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 3;
}
.orbit > * {
  position: absolute;
}
.badge {
  background: #fff;
  color: var(--blue);
  border-radius: 18px;
  padding: 10px 16px;
  font-weight: 700;
  font-size: 0.9rem;
  box-shadow: 0 14px 30px rgba(0, 0, 0, 0.2);
  display: flex;
  gap: 8px;
  align-items: center;
  z-index: 2;
}
.badge small {
  display: block;
  font-weight: 500;
  color: #6b7690;
  font-size: 0.7rem;
}
.badge.b2 {
  background: var(--blue);
  color: #fff;
  left: 1%;
  bottom: 5%;
}
.badge.b2 small {
  color: var(--deco);
}
.badge.b1 {
  left: -3%;
  top: 9%;
}
.b1 .ic {
  color: var(--red);
  width: 1.6em;
  height: 1.6em;
}
.b2 .ic {
  width: 1.3em;
  height: 1.3em;
}
.price {
  right: -1%;
  bottom: 24%;
  z-index: 2;
  width: 104px;
  height: 104px;
  border-radius: 50%;
  background: var(--sky);
  color: #fff;
  display: grid;
  place-items: center;
  text-align: center;
  font-weight: 800;
  line-height: 1.1;
  font-size: 1.1rem;
  box-shadow: 0 12px 26px rgba(8, 152, 232, 0.5);
  transform: rotate(12deg);
  border: 4px solid #fff;
}
.price small {
  display: block;
  font-size: 0.62rem;
  font-weight: 600;
  letter-spacing: 0.1em;
}

/* ===== Tablet & Mobile ===== */
@media (max-width: 900px) {
  .hero {
    grid-template-columns: minmax(0, 1fr);
    text-align: left;
    gap: 30px;
    padding-top: 28px;
    padding-bottom: 128px;
  }
  .copy,
  .visual {
    min-width: 0;
  }
  .hwave {
    height: 110px;
  }
  .wm {
    width: 50vw;
  }
  .visual {
    order: -1;
    max-width: 520px;
    margin: 0 auto clamp(28px, 9vw, 56px);
  }
  .visual::before {
    width: 92%;
    right: -8%;
  }
  .orbit .badge {
    font-size: 0.72rem;
    padding: 7px 11px;
  }
  .orbit .price {
    width: 78px;
    height: 78px;
    font-size: 0.9rem;
  }
  .eyebrow {
    gap: 10px;
    letter-spacing: 0.18em;
    font-size: clamp(0.6rem, 2.9vw, 0.76rem);
    white-space: nowrap;
    margin-bottom: 12px;
  }
  .eyebrow::before {
    width: 26px;
    flex: none;
  }
  h1 {
    overflow-wrap: anywhere;
  }
  .cta {
    flex-wrap: nowrap;
    gap: 8px;
  }
  .cta .btn {
    flex: 1 1 0;
    min-width: 0;
    justify-content: center;
    gap: 6px;
    padding: 13px 8px;
    font-size: clamp(0.74rem, 3.7vw, 0.92rem);
    white-space: nowrap;
  }
  .cta .btn .ic {
    width: 1em;
    height: 1em;
  }
  .chips {
    margin-top: 22px;
  }
}
</style>