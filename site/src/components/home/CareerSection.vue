<script setup lang="ts">
import { ClipboardList, Mail, MessageCircle, Star, Users } from 'lucide-vue-next'
import logo from '@/assets/images/logo.jpeg'
import crewPhoto from '@/assets/images/crew.jpeg'

// ===== Data Karier =====
const APPLY_SUBJECT = 'Lamaran%20Crew%20Restoran%20IwaGeprek'

const career = {
  title: 'Bergabung Bersama',
  highlight: 'IwaGeprek',
  subtitle: 'Tumbuh bersama tim yang penuh semangat.',
  role: 'Crew Restoran',
  rolePill: 'Posisi Tersedia',
  duties: [
    'Melayani pelanggan dengan ramah',
    'Menyiapkan pesanan dan menjaga kualitas penyajian',
    'Menjaga kebersihan area kerja',
    'Bekerja sama dengan tim',
  ],
  criteria: [
    'Disiplin dan bertanggung jawab',
    'Komunikatif dan ramah',
    'Mampu bekerja dalam tim',
    'Bersedia belajar hal baru',
  ],
  applyTitle: 'Cara Melamar',
  applyText: 'Kirimkan lamaran dan CV Anda ke',
  ctaQuestion: 'Tertarik bergabung?',
  whatsappLabel: 'Hubungi via WhatsApp',
  whatsappUrl:
    'https://wa.me/6285736882888?text=Halo%20IwaGeprek%2C%20saya%20tertarik%20melamar%20sebagai%20Crew%20Restoran.',
  emailLabel: 'Kirim Email',
  emailUrl: `mailto:hi.iwageprek@gmail.com?subject=${APPLY_SUBJECT}`,
}

const careerPhoto = { src: crewPhoto, alt: 'Crew IwaGeprek di depan ruko' }
</script>

<template>
  <section id="karier" class="join">
    <!-- Gelombang merah + biru tua di bagian atas section -->
    <svg class="jwave" viewBox="0 0 1440 90" preserveAspectRatio="none" aria-hidden="true">
      <path d="M0 0H1440V70C1250 90 1000 38 760 58C520 78 220 70 0 44Z" fill="#CC0B14" />
      <path d="M0 0H1440V44C1220 70 960 16 700 36C440 56 200 50 0 22Z" fill="#083878" />
    </svg>

    <div class="wrap jgrid">
      <div class="jtop">
        <div class="jbrand">
          <img :src="logo" alt="Logo IwaGeprek" /><span>{{ career.highlight }}</span>
        </div>
        <h2 class="jtitle">
          <span class="b">{{ career.title }}</span>
          <span class="r">{{ career.highlight }}</span>
        </h2>
        <p class="jsub">{{ career.subtitle }}</p>
      </div>

      <div class="jl">
        <div class="jcard">
          <div class="jhead">
            <Users aria-hidden="true" />
            <b>{{ career.role }}</b>
            <span class="jpill">{{ career.rolePill }}</span>
          </div>
          <div class="jbody">
            <div class="jcol">
              <h3>
                <span class="ji"><ClipboardList aria-hidden="true" /></span>Tugas Utama
              </h3>
              <ul>
                <li v-for="duty in career.duties" :key="duty">
                  <svg class="ck" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="11" fill="#CC0B14" /><path d="M7 12.5l3.2 3.2L17 9" fill="none" stroke="#fff" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" /></svg><span>{{ duty }}</span>
                </li>
              </ul>
            </div>
            <div class="jcol">
              <h3>
                <span class="ji"><Star fill="currentColor" aria-hidden="true" /></span>Kriteria
              </h3>
              <ul>
                <li v-for="item in career.criteria" :key="item">
                  <svg class="ck" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="11" fill="#CC0B14" /><path d="M7 12.5l3.2 3.2L17 9" fill="none" stroke="#fff" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" /></svg><span>{{ item }}</span>
                </li>
              </ul>
            </div>
          </div>
          <div class="japply">
            <Mail aria-hidden="true" />
            <div>
              <b>{{ career.applyTitle }}</b>
              <span>
                {{ career.applyText }}
                <a :href="career.emailUrl">hi.iwageprek@gmail.com</a>
              </span>
            </div>
          </div>
        </div>

        <div class="jcta">
          <span class="jq"><Users aria-hidden="true" />{{ career.ctaQuestion }}</span>
          <div class="jbtns">
            <a class="btn" :href="career.whatsappUrl" target="_blank" rel="noopener">
              <MessageCircle class="ic" aria-hidden="true" /> {{ career.whatsappLabel }}
            </a>
            <a class="btn o" :href="career.emailUrl">
              <Mail class="ic" aria-hidden="true" /> {{ career.emailLabel }}
            </a>
          </div>
        </div>
      </div>

      <!-- Foto crew: disembunyikan di tablet/mobile (sesuai desain) -->
      <div class="jvisual">
        <img class="team" :src="careerPhoto.src" :alt="careerPhoto.alt" width="1000" height="915" loading="lazy" />
      </div>
    </div>
  </section>
</template>

<style scoped>
.join {
  position: relative;
  overflow: hidden;
  container-type: inline-size;
  background: #fdfdfd;
  padding: 170px 0 100px;
  line-height: 1.6;
  font-size: 17px;
}
.jwave {
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  width: 100%;
  height: 90px;
  z-index: 0;
  pointer-events: none;
}
.jgrid {
  position: relative;
  display: grid;
  grid-template-columns: 1.3fr 1fr;
  gap: 44px;
  align-items: stretch;
  row-gap: 40px;
}
.jtop {
  grid-column: 1/-1;
  text-align: center;
}
.jbrand {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  font-weight: 700;
  color: var(--blue);
  font-size: 1.5rem;
  margin-bottom: 14px;
}
.jbrand img {
  width: 46px;
  height: auto;
}
.jtitle {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  align-items: baseline;
  gap: 0 0.3em;
  text-align: center;
  font-size: clamp(2.2rem, 4.6vw, 3.8rem);
  font-weight: 800;
  line-height: 1.15;
  letter-spacing: -0.02em;
}
.jtitle .b {
  display: inline-block;
  color: var(--blue);
}
.jtitle .r {
  display: inline-block;
  color: var(--red);
  font-style: italic;
  position: relative;
}
.jtitle .r::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: 2px;
  height: 5px;
  border-radius: 5px;
  background: var(--red);
}
.jsub {
  font-weight: 600;
  color: var(--blue);
  font-size: 1.2rem;
  margin: 14px 0 26px;
  text-align: center;
}
.jl {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}
.jcard {
  border-radius: 28px;
  background: #fff;
  border: 2px solid #fff;
  box-shadow: 0 20px 44px rgba(1, 93, 247, 0.14);
  overflow: hidden;
}
.jhead {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
  background: var(--blue);
  color: #fff;
  padding: 16px 26px;
}
.jhead svg {
  width: 34px;
  height: 34px;
}
.jhead b {
  font-size: 1.5rem;
  font-weight: 800;
}
.jpill {
  background: var(--red);
  padding: 6px 18px;
  border-radius: 99px;
  font-weight: 700;
  font-size: 0.9rem;
}
.jbody {
  display: grid;
  grid-template-columns: 1fr 1fr;
  padding: 24px 26px;
}
.jcol:first-child {
  padding-right: 24px;
}
.jcol + .jcol {
  border-left: 2px solid var(--deco);
  padding-left: 26px;
}
.jcol h3 {
  display: flex;
  align-items: center;
  gap: 10px;
  background: var(--deco);
  color: var(--blue);
  font-weight: 800;
  font-size: 1.05rem;
  border-radius: 99px;
  padding: 5px 20px 5px 5px;
  margin-bottom: 16px;
  width: max-content;
  max-width: 100%;
}
.ji {
  flex: none;
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: var(--red);
  display: grid;
  place-items: center;
  color: #fff;
}
.ji svg {
  width: 20px;
  height: 20px;
}
.jcol ul {
  list-style: none;
  padding: 0;
  display: grid;
  gap: 10px;
}
.jcol li {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  color: var(--blue);
  font-weight: 500;
  font-size: 0.95rem;
  line-height: 1.4;
}
.ck {
  flex: none;
  width: 22px;
  height: 22px;
}
.japply {
  display: flex;
  gap: 14px;
  align-items: center;
  margin: 0 26px 24px;
  padding: 14px 18px;
  border-radius: 18px;
  background: var(--deco);
}
.japply > svg {
  flex: none;
  width: 30px;
  height: 30px;
  color: var(--red);
}
.japply b {
  display: block;
  color: var(--blue);
}
.japply span {
  color: var(--muted);
  font-size: 0.93rem;
}
.japply a {
  color: var(--red);
  font-weight: 700;
  text-decoration: none;
  word-break: normal;
  overflow-wrap: anywhere;
}
.jcta {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14px;
  flex-wrap: wrap;
  margin-top: 26px;
}
.jq {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  font-weight: 800;
  color: var(--blue);
  font-size: 1.25rem;
  flex-basis: 100%;
  margin: 0 0 4px;
}
.jq svg {
  width: 34px;
  height: 34px;
}
.jbtns {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  align-items: stretch;
  justify-content: center;
}
.jbtns .btn {
  padding: 12px 28px;
  border-radius: 999px;
}

/* Foto crew: menembus sampai tepi kanan layar (container query) */
.jvisual {
  --gx: max(24px, calc((100cqw - 1132px) / 2));
  position: relative;
  display: block;
  width: calc(100% + var(--gx));
  margin-right: calc(-1 * var(--gx));
  max-width: none;
  align-self: stretch;
  min-height: 0;
  overflow: visible;
}
.jvisual .team {
  position: absolute;
  right: 0;
  bottom: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: right bottom;
  filter: drop-shadow(0 18px 26px rgba(1, 93, 247, 0.22));
}

@media (max-width: 900px) {
  .join {
    padding: 110px 0 56px;
  }
  .jwave {
    height: 50px;
  }
  .jgrid {
    grid-template-columns: minmax(0, 1fr);
    row-gap: 28px;
  }
  .jgrid > * {
    min-width: 0;
  }
  .jtitle {
    font-size: clamp(1.9rem, 8.5vw, 2.6rem);
  }
  .jcard,
  .jbody {
    min-width: 0;
  }
  .jbtns {
    width: 100%;
    max-width: 520px;
    margin: 0 auto;
    gap: 10px;
  }
  .jbtns .btn {
    flex: 1 1 130px;
    justify-content: center;
    white-space: nowrap;
    font-size: 0.92rem;
    padding: 12px;
  }
  .jvisual {
    display: none;
  }
}
@media (max-width: 620px) {
  .jbody {
    grid-template-columns: 1fr;
    gap: 22px;
  }
  .jcol:first-child {
    padding-right: 0;
  }
  .jcol + .jcol {
    border-left: 0;
    padding-left: 0;
    border-top: 2px solid var(--deco);
    padding-top: 20px;
  }
  .jhead b {
    font-size: 1.25rem;
  }
}
@media (max-width: 600px) {
  .japply {
    margin: 0 16px 20px;
    padding: 12px 14px;
  }
  .japply a {
    font-size: 0.84rem;
  }
  .jq {
    font-size: 1.1rem;
  }
}
@media (max-width: 480px) {
  .jbtns .btn {
    flex: 1 1 100%;
  }
}
@media (max-width: 420px) {
  .jsub {
    font-size: 0.95rem;
  }
}
</style>