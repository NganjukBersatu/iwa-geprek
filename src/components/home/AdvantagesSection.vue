<script setup lang="ts">
import { ChefHat, ConciergeBell, Fish, Flame, Users } from 'lucide-vue-next'
import ikanSegar from '@/assets/images/keunggulan-ikan-segar.jpg'
import sambalKhas from '@/assets/images/keunggulan-sambal-khas.jpg'
import rasaLezat from '@/assets/images/keunggulan-rasa-lezat.jpg'
import digorengCrispy from '@/assets/images/keunggulan-digoreng-crispy.jpg'
import penyajianMenarik from '@/assets/images/keunggulan-penyajian-menarik.jpg'
import tempatNyaman from '@/assets/images/keunggulan-tempat-nyaman.jpg'

// ===== Data Keunggulan =====
const advantagesIntro = {
  titleBlue: 'Keunggulan',
  titleRed: 'Kami',
  subtitle: 'Alasan kenapa IWAGEPREK selalu jadi pilihan terbaik!',
}

const advantages = [
  {
    id: 'ikan-segar',
    title: 'Ikan Segar',
    description: 'Menggunakan ikan segar pilihan untuk menjaga kualitas dan cita rasa.',
    image: ikanSegar,
    imageAlt: 'Ikan Segar',
    icon: Fish,
  },
  {
    id: 'sambal-khas',
    title: 'Sambal Khas',
    description: 'Sambal dengan racikan bumbu khas yang menggugah selera.',
    image: sambalKhas,
    imageAlt: 'Sambal Khas',
    icon: Flame,
  },
  {
    id: 'rasa-lezat',
    title: 'Rasa Lezat',
    description: 'Perpaduan bumbu dan ikan yang menghasilkan cita rasa istimewa.',
    image: rasaLezat,
    imageAlt: 'Rasa Lezat',
    icon: ChefHat,
  },
  {
    id: 'digoreng-crispy',
    title: 'Digoreng Crispy',
    description: 'Digoreng hingga garing dan renyah di luar, tetap juicy di dalam.',
    image: digorengCrispy,
    imageAlt: 'Digoreng Crispy',
    icon: Flame,
  },
  {
    id: 'penyajian-menarik',
    title: 'Penyajian Menarik',
    description: 'Disajikan dengan tampilan menarik dan pelengkap yang menggugah selera.',
    image: penyajianMenarik,
    imageAlt: 'Penyajian Menarik',
    icon: ConciergeBell,
  },
  {
    id: 'tempat-nyaman',
    title: 'Tempat Nyaman',
    description: 'Suasana bersantap yang nyaman untuk menikmati hidangan bersama keluarga.',
    image: tempatNyaman,
    imageAlt: 'Tempat Nyaman',
    icon: Users,
  },
]
</script>

<template>
  <section id="keunggulan" class="adv">
    <!-- Gelombang dasar section -->
    <svg class="wb" viewBox="0 0 1440 130" preserveAspectRatio="none" aria-hidden="true">
      <path fill="#CC0B14" d="M900 130C1100 40 1300 20 1440 40V130Z" />
      <path fill="#083878" d="M0 130V80C300 20 650 120 1050 70C1200 52 1340 60 1440 80V130Z" />
    </svg>
    <!-- Siluet ikan dekoratif -->
    <svg class="ghost" viewBox="0 0 60 30" aria-hidden="true">
      <path fill="currentColor" d="M2 15C10 2 32 0 46 15 32 30 10 28 2 15Z" />
      <path fill="currentColor" d="M44 15 58 4c-2 4-2 18 0 22Z" />
      <circle cx="13" cy="12" r="2" fill="#fff" />
    </svg>
    <!-- bob: tetesan air -->
    <svg class="drop e1 animate-bob motion-reduce:animate-none" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2C12 2 4 11 4 16a8 8 0 0 0 16 0c0-5-8-14-8-14Z" /></svg>
    <svg class="drop e2 animate-bob motion-reduce:animate-none" viewBox="0 0 24 24" aria-hidden="true" style="animation-delay: -2s"><path d="M12 2C12 2 4 11 4 16a8 8 0 0 0 16 0c0-5-8-14-8-14Z" /></svg>
    <svg class="drop e3 animate-bob motion-reduce:animate-none" viewBox="0 0 24 24" aria-hidden="true" style="animation-delay: -3s"><path d="M12 2C12 2 4 11 4 16a8 8 0 0 0 16 0c0-5-8-14-8-14Z" /></svg>

    <div class="wrap">
      <header class="advhead">
        <h2><span class="b">{{ advantagesIntro.titleBlue }}</span> <span class="r">{{ advantagesIntro.titleRed }}</span></h2>
        <p class="advsub">{{ advantagesIntro.subtitle }}</p>
        <svg class="swoosh" viewBox="0 0 280 16" aria-hidden="true">
          <path
            d="M2 12C70 2 170 2 278 8"
            fill="none"
            stroke="#CC0B14"
            stroke-width="3.5"
            stroke-linecap="round"
          />
        </svg>
      </header>

      <div class="feats">
        <!-- Lift + shadow expand saat hover -->
        <article v-for="item in advantages" :key="item.id" class="feat">
          <div class="fp">
            <img :src="item.image" :alt="item.imageAlt" width="180" height="180" loading="lazy" />
            <span class="fb"><component :is="item.icon" aria-hidden="true" /></span>
          </div>
          <div class="ft">
            <h3>{{ item.title }}</h3>
            <p>{{ item.description }}</p>
          </div>
        </article>
      </div>
    </div>
  </section>
</template>

<style scoped>
.adv {
  position: relative;
  overflow: hidden;
  background: #fdfdfd;
  padding: 90px 0 200px;
  text-align: left;
  margin-top: -1px;
  line-height: 1.6;
  font-size: 17px;
}
.wb {
  position: absolute;
  left: 0;
  width: 100%;
  pointer-events: none;
  bottom: 0;
  height: 130px;
}
.ghost {
  position: absolute;
  right: 3%;
  top: 40px;
  width: min(30vw, 380px);
  color: var(--color-brand-ghost);
  transform: rotate(-10deg);
}
.drop {
  width: 40px;
  opacity: 0.8;
}
.e1 {
  right: 34%;
  top: 60px;
  transform: rotate(-25deg);
}
.e2 {
  right: 2%;
  top: 70px;
  width: 30px;
}
.e3 {
  right: 6%;
  top: 210px;
  width: 26px;
}
.wrap {
  position: relative;
  z-index: 1;
}

.advhead h2 {
  font-size: clamp(2.6rem, 6vw, 4.8rem);
  font-style: italic;
  font-weight: 800;
  line-height: 1.02;
  letter-spacing: -0.02em;
  color: var(--blue);
}
.advhead .b {
  color: var(--blue);
}
.advhead .r {
  color: var(--red);
}
.advsub {
  margin-top: 14px;
  font-style: italic;
  font-weight: 500;
  font-size: 1.2rem;
  color: rgba(1, 93, 247, 0.85);
}
.swoosh {
  display: block;
  width: min(280px, 60%);
  margin-top: 10px;
}

.feats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  margin-top: 48px;
}
.feat {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 20px 22px 20px 20px;
  border-radius: 30px;
  border: 2px solid #fff;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.95), rgba(238, 246, 252, 0.92));
  box-shadow: 0 16px 36px rgba(8, 152, 232, 0.14);
  transition:
    transform 0.3s,
    box-shadow 0.3s;
}
.feat:hover {
  transform: translateY(-6px);
  box-shadow: 0 22px 44px rgba(8, 152, 232, 0.24);
}
.fp {
  position: relative;
  flex: none;
  width: 150px;
  height: 150px;
}
.fp img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
  box-shadow:
    0 0 0 3px #fff,
    0 0 0 5px var(--sky);
}
.fb {
  position: absolute;
  right: -9px;
  bottom: 6px;
  width: 60px;
  height: 60px;
  border: 3px solid #fff;
  border-radius: 50%;
  background: var(--blue);
  color: #fff;
  display: grid;
  place-items: center;
  box-shadow: 0 6px 14px rgba(1, 93, 247, 0.3);
}
.fb svg {
  width: 26px;
  height: 26px;
}
.ft h3 {
  font-size: 1.2rem;
  font-weight: 800;
  color: var(--blue);
  line-height: 1.2;
  margin-bottom: 6px;
}
.ft p {
  color: var(--muted);
  font-size: 0.93rem;
  line-height: 1.5;
}

@media (max-width: 1100px) {
  .feats {
    grid-template-columns: repeat(2, 1fr);
  }
}
@media (max-width: 900px) {
  .wb {
    height: 80px;
  }
  .advhead h2 {
    overflow-wrap: anywhere;
  }
}
@media (max-width: 700px) {
  .adv {
    padding: 40px 0 120px;
  }
  .ghost {
    width: 200px;
    opacity: 0.7;
  }
  .drop {
    display: none;
  }
  .advhead h2 {
    font-size: 2.4rem;
  }
  .advsub {
    font-size: 1rem;
    margin-top: 10px;
  }
  .swoosh {
    width: 150px;
  }
  .feats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
    margin-top: 28px;
  }
  .feat {
    flex-direction: column;
    text-align: center;
    gap: 10px;
    padding: 16px 10px;
    border-radius: 22px;
  }
  .fp {
    width: 84px;
    height: 84px;
  }
  .fb {
    width: 32px;
    height: 32px;
    right: -6px;
    bottom: 0;
    border-width: 2px;
  }
  .fb svg {
    width: 15px;
    height: 15px;
  }
  .ft h3 {
    font-size: 0.95rem;
    margin-bottom: 4px;
  }
  .ft p {
    font-size: 0.76rem;
    line-height: 1.4;
  }
}
</style>