import imgDoriGeprekSambalMatah from '@/assets/images/menu-dori-geprek-sambal-matah.jpg'
import imgGurameGorengGeprek from '@/assets/images/menu-gurame-goreng-geprek.jpg'
import imgNilaBakarSambalKomplit from '@/assets/images/menu-nila-bakar-sambal-komplit.jpg'
import imgIkanBakarBumbuMerah from '@/assets/images/menu-ikan-bakar-bumbu-merah.jpg'
import imgIkanGorengSambalTomat from '@/assets/images/menu-ikan-goreng-sambal-tomat.jpg'
import imgCumiBumbuSambalMerah from '@/assets/images/menu-cumi-bumbu-sambal-merah.jpg'
import imgBebekGorengSambal from '@/assets/images/menu-bebek-goreng-sambal.jpg'
import imgCapcayKuah from '@/assets/images/menu-capcay-kuah.jpg'
import imgTumisKangkung from '@/assets/images/menu-tumis-kangkung.jpg'
import imgEsJerukSegar from '@/assets/images/menu-es-jeruk-segar.jpg'
import imgUdangSausPadangJagung from '@/assets/images/menu-udang-saus-padang-jagung.jpg'
import imgSateUdangBakarMadu from '@/assets/images/menu-sate-udang-bakar-madu.jpg'
import imgAyamBakarSambalTomat from '@/assets/images/menu-ayam-bakar-sambal-tomat.jpg'
import imgTahuTempeGoreng from '@/assets/images/menu-tahu-tempe-goreng.jpg'
import imgNilaBakarDabuDabu from '@/assets/images/menu-nila-bakar-dabu-dabu.jpg'
import imgNilaGorengSambalKecap from '@/assets/images/menu-nila-goreng-sambal-kecap.jpg'
import imgLeleGorengSambalTerasi from '@/assets/images/menu-lele-goreng-sambal-terasi.jpg'
import imgIkanGorengSambalMangga from '@/assets/images/menu-ikan-goreng-sambal-mangga.jpg'
import imgNilaBakarSambalTrio from '@/assets/images/menu-nila-bakar-sambal-trio.jpg'
import imgGurameGorengSambalTomat from '@/assets/images/menu-gurame-goreng-sambal-tomat.jpg'
import hero from '@/assets/images/hero.jpg'
import lodeh from '@/assets/images/lodeh.jpg'
import kepiting from '@/assets/images/kepiting.jpeg'
import air from '@/assets/images/air.jpeg'
import teh from '@/assets/images/teh.jpeg'

export type FilterKey = 'all' | 'Goreng' | 'Bakar' | 'Seafood' | 'Sayur' | 'Minuman'

export interface MenuItem {
  id: string
  name: string
  description: string
  /** Harga dalam Rupiah (angka penuh, mis. 28000). */
  price: number
  category: Exclude<FilterKey, 'all'>
  image: string
  imageAlt: string
}

/** Format angka menjadi Rupiah, mis. 28000 → "Rp 28.000". */
export function formatRupiah(value: number): string {
  return `Rp ${value.toLocaleString('id-ID')}`
}

export const menuIntro = {
  title: 'Menu andalan kami',
  fullTitle: 'Menu Lengkap',
  subtitle: 'Semua menu disajikan dengan nasi hangat, lalapan, dan sambal pilihan.',
}

export const menuFilters: { key: FilterKey; label: string }[] = [
  { key: 'all', label: 'Semua' },
  { key: 'Goreng', label: 'Goreng' },
  { key: 'Bakar', label: 'Bakar' },
  { key: 'Seafood', label: 'Seafood' },
  { key: 'Sayur', label: 'Sayur' },
  { key: 'Minuman', label: 'Minuman' },
]

/** Jumlah menu yang tampil di preview Beranda (3 menu pertama, sesuai desain). */
export const PREVIEW_COUNT = 3

export const menuItems: MenuItem[] = [
  {
    id: 'dori-geprek-sambal-matah',
    name: "Dori geprek sambal matah",
    description: "Fillet dori berbalut tepung renyah, ditaburi sambal matah serai, bawang merah, dan cabai iris.",
    price: 28000,
    category: 'Goreng',
    image: imgDoriGeprekSambalMatah,
    imageAlt: "Ikan dori geprek sambal matah",
  },
  {
    id: 'gurame-goreng-geprek',
    name: "Gurame goreng geprek",
    description: "Gurame utuh digoreng garing, disajikan dengan tempe dan sambal terasi.",
    price: 65000,
    category: 'Goreng',
    image: hero,
    imageAlt: "Gurame goreng geprek di atas selada hijau",
  },
  {
    id: 'nila-bakar-sambal-komplit',
    name: "Nila bakar sambal komplit",
    description: "Nila dibakar dengan kecap manis dan bumbu rempah, ditemani tiga sambal.",
    price: 48000,
    category: 'Bakar',
    image: imgNilaBakarSambalKomplit,
    imageAlt: "Nila bakar dengan aneka sambal di atas daun pisang",
  },
  {
    id: 'ikan-bakar-bumbu-merah',
    name: "Ikan bakar bumbu merah",
    description: "Dibelah, dibumbui, lalu dibakar sampai pinggirnya karamel.",
    price: 45000,
    category: 'Bakar',
    image: imgIkanBakarBumbuMerah,
    imageAlt: "Ikan bakar bumbu merah dengan sambal dan timun",
  },
  {
    id: 'ikan-goreng-sambal-tomat',
    name: "Ikan goreng sambal tomat",
    description: "Ikan goreng berkulit garing dengan sambal tomat segar dan perasan jeruk nipis.",
    price: 38000,
    category: 'Goreng',
    image: imgIkanGorengSambalTomat,
    imageAlt: "Ikan goreng dengan sambal tomat dan irisan jeruk nipis",
  },
  {
    id: 'cumi-bumbu-sambal-merah',
    name: "Cumi bumbu sambal merah",
    description: "Cumi segar dibelah, dibumbui sambal merah pedas manis dan dibakar harum.",
    price: 32000,
    category: 'Seafood',
    image: imgCumiBumbuSambalMerah,
    imageAlt: "Cumi bumbu sambal merah",
  },
  {
    id: 'kepiting',
    name: "Kepiting Lada Hitam Spesial",
    description: "Kepiting dengan bumbu lada hitam.",
    price: 50000,
    category: 'Seafood',
    image: kepiting,
    imageAlt: "kepiting",
  },
  {
    id: 'bebek-goreng-sambal',
    name: "Bebek goreng sambal",
    description: "Bebek empuk berbumbu rempah digoreng kering, dengan sambal merah dan nasi hangat.",
    price: 38000,
    category: 'Goreng',
    image: imgBebekGorengSambal,
    imageAlt: "Bebek goreng sambal",
  },
  {
    id: 'capcay-kuah',
    name: "Capcay kuah",
    description: "Aneka sayur segar dan jamur kuping dalam kuah gurih yang hangat.",
    price: 18000,
    category: 'Sayur',
    image: imgCapcayKuah,
    imageAlt: "Capcay kuah",
  },
  {
    id: 'tumis-kangkung',
    name: "Tumis kangkung",
    description: "Kangkung segar ditumis api besar dengan bawang putih dan cabai merah.",
    price: 12000,
    category: 'Sayur',
    image: imgTumisKangkung,
    imageAlt: "Tumis kangkung",
  },
   {
    id: 'lodeh',
    name: "Sayur Lodeh",
    description: "Hidangan berkuah santan khas Indonesia",
    price: 15000,
    category: 'Sayur',
    image: lodeh,
    imageAlt: "Sayur Lodeh",
  },
  {
    id: 'es-jeruk-segar',
    name: "Es jeruk segar",
    description: "Perasan jeruk asli, es batu, dan daun mint. Segar untuk teman pedas.",
    price: 8000,
    category: 'Minuman',
    image: imgEsJerukSegar,
    imageAlt: "Es jeruk segar",
  },
  {
    id: 'air',
    name: "Air mineral",
    description: "Air mineral aqua.",
    price: 3000,
    category: 'Minuman',
    image: air,
    imageAlt: "air",
  },
  {
    id: 'teh',
    name: "Es teh manis",
    description: "Es teh manis gula asli.",
    price: 5000,
    category: 'Minuman',
    image: teh,
    imageAlt: "teh",
  },
  {
    id: 'udang-saus-padang-jagung',
    name: "Udang saus padang jagung",
    description: "Udang dan jagung manis dalam saus padang pedas yang kental.",
    price: 35000,
    category: 'Seafood',
    image: imgUdangSausPadangJagung,
    imageAlt: "Udang saus padang jagung",
  },
  {
    id: 'sate-udang-bakar-madu',
    name: "Sate udang bakar madu",
    description: "Udang tusuk dibakar dengan olesan madu manis, disajikan bersama lalapan.",
    price: 28000,
    category: 'Bakar',
    image: imgSateUdangBakarMadu,
    imageAlt: "Sate udang bakar madu",
  },
  {
    id: 'ayam-bakar-sambal-tomat',
    name: "Ayam bakar sambal tomat",
    description: "Ayam bakar bumbu kecap yang meresap, ditemani sambal tomat segar.",
    price: 25000,
    category: 'Bakar',
    image: imgAyamBakarSambalTomat,
    imageAlt: "Ayam bakar sambal tomat",
  },
  {
    id: 'tahu-tempe-goreng',
    name: "Tahu tempe goreng",
    description: "Tahu dan tempe goreng garing, pelengkap sempurna untuk nasi dan sambal.",
    price: 10000,
    category: 'Goreng',
    image: imgTahuTempeGoreng,
    imageAlt: "Tahu tempe goreng",
  },
  {
    id: 'nila-bakar-dabu-dabu',
    name: "Nila bakar dabu-dabu",
    description: "Nila bakar utuh di atas daun pisang dengan sambal dabu-dabu segar.",
    price: 40000,
    category: 'Bakar',
    image: imgNilaBakarDabuDabu,
    imageAlt: "Nila bakar dabu-dabu",
  },
  {
    id: 'nila-goreng-sambal-kecap',
    name: "Nila goreng sambal kecap",
    description: "Nila goreng renyah dengan sambal kecap pedas, bawang, dan jeruk limau.",
    price: 35000,
    category: 'Goreng',
    image: imgNilaGorengSambalKecap,
    imageAlt: "Nila goreng sambal kecap",
  },
  {
    id: 'lele-goreng-sambal-terasi',
    name: "Lele goreng sambal terasi",
    description: "Lele goreng gurih dengan sambal terasi, terong, dan lalapan segar.",
    price: 22000,
    category: 'Goreng',
    image: imgLeleGorengSambalTerasi,
    imageAlt: "Lele goreng sambal terasi",
  },
  {
    id: 'ikan-goreng-sambal-mangga',
    name: "Ikan goreng sambal mangga",
    description: "Ikan goreng garing disiram sambal mangga muda yang segar dan pedas.",
    price: 38000,
    category: 'Goreng',
    image: imgIkanGorengSambalMangga,
    imageAlt: "Ikan goreng sambal mangga",
  },
  {
    id: 'nila-bakar-sambal-trio',
    name: "Nila bakar sambal trio",
    description: "Nila bakar komplet dengan tiga sambal pilihan, tempe goreng, dan lalapan.",
    price: 45000,
    category: 'Bakar',
    image: imgNilaBakarSambalTrio,
    imageAlt: "Nila bakar sambal trio",
  },
  {
    id: 'gurame-goreng-sambal-tomat',
    name: "Gurame goreng sambal tomat",
    description: "Gurame utuh digoreng garing, disajikan dengan sambal tomat dan lalapan.",
    price: 60000,
    category: 'Goreng',
    image: imgGurameGorengSambalTomat,
    imageAlt: "Gurame goreng sambal tomat",
  },
]