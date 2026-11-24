import imgKulitPatinCrispy from '@/assets/images/kulit-patin.png'
import imgPatinCrispy from '@/assets/images/patin.png'
import imgKulitSalmonCrispy from '@/assets/images/kulit-salmon.png'
import imgSalmonCrispy from '@/assets/images/salmon.png'
import imgNasiPutih from '@/assets/images/menu-nasi-putih.jpg'
import imgNasiDaunJeruk from '@/assets/images/menu-nasi-daun-jeruk.jpg'
import imgSambalGeprek from '@/assets/images/menu-sambal-geprek.jpg'
import imgSambalIjo from '@/assets/images/menu-sambal-ijo.jpg'
import imgSausSachet from '@/assets/images/menu-saus-sachet.jpg'

export type FilterKey = 'all' | 'Anti Ayam' | 'Tambahan'

export interface PriceOption {
  label: string
  /** Harga dalam Rupiah (angka penuh, mis. 9000). */
  price: number
}

export interface MenuVariant {
  name: string
  /** 'geprek' = label biru, 'api' = label merah (sesuai gambar menu). */
  tone: 'geprek' | 'api'
  options: PriceOption[]
}

export interface MenuItem {
  id: string
  name: string
  category: Exclude<FilterKey, 'all'>
  /** Menu utama: punya beberapa varian harga. */
  variants?: MenuVariant[]
  /** Menu tambahan: harga tunggal. */
  price?: number
  image?: string
  imageAlt?: string
}

/** Format angka menjadi Rupiah, mis. 28000 → "Rp 28.000". */
export function formatRupiah(value: number): string {
  return `Rp ${value.toLocaleString('id-ID')}`
}

export const menuIntro = {
  title: 'Menu Anti Ayam',
  fullTitle: 'Menu Lengkap',
  subtitle: 'Pilih sambal geprek/ijo atau saus laut api, dengan nasi putih atau nasi daun jeruk.',
}

export const menuFilters: { key: FilterKey; label: string }[] = [
  { key: 'all', label: 'Semua' },
  { key: 'Anti Ayam', label: 'Anti Ayam' },
  { key: 'Tambahan', label: 'Tambahan' },
]

/** Jumlah menu yang tampil di preview Beranda (3 menu anti ayam). */
export const PREVIEW_COUNT = 3

const sambalGeprek = (tanpaNasi: number, putih: number, daunJeruk: number): MenuVariant => ({
  name: 'Sambal Geprek/Ijo',
  tone: 'geprek',
  options: [
    { label: 'Tanpa nasi', price: tanpaNasi },
    { label: '+ Nasi putih', price: putih },
    { label: '+ Nasi daun jeruk', price: daunJeruk },
  ],
})

const sausLautApi = (tanpaNasi: number, putih: number): MenuVariant => ({
  name: 'Saus Laut Api',
  tone: 'api',
  options: [
    { label: 'Tanpa nasi', price: tanpaNasi },
    { label: '+ Nasi putih', price: putih },
  ],
})

export const menuItems: MenuItem[] = [
  {
    id: 'kulit-patin-crispy',
    name: 'Kulit Patin Crispy',
    category: 'Anti Ayam',
    image: imgKulitPatinCrispy,
    imageAlt: 'Kulit patin crispy',
    variants: [sambalGeprek(9000, 11000, 14000), sausLautApi(11000, 14000)],
  },
  {
    id: 'patin-crispy',
    name: 'Patin Crispy',
    category: 'Anti Ayam',
    image: imgPatinCrispy,
    imageAlt: 'Patin crispy',
    variants: [sambalGeprek(11000, 13000, 16000), sausLautApi(13000, 16000)],
  },
  {
    id: 'kulit-salmon-crispy',
    name: 'Kulit Salmon Crispy',
    category: 'Anti Ayam',
    image: imgKulitSalmonCrispy,
    imageAlt: 'Kulit salmon crispy',
    variants: [sambalGeprek(11000, 13000, 16000), sausLautApi(13000, 16000)],
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
    id: 'salmon-crispy',
    name: 'Salmon Crispy',
    category: 'Anti Ayam',
    image: imgSalmonCrispy,
    imageAlt: 'Salmon crispy',
    variants: [sambalGeprek(13000, 15000, 18000), sausLautApi(15000, 18000)],
  },

    // Menu tambahan
  { id: 'nasi-putih', name: 'Nasi Putih', category: 'Tambahan', price: 4000,
    image: imgNasiPutih, imageAlt: 'Nasi putih' },
  { id: 'nasi-daun-jeruk', name: 'Nasi Daun Jeruk', category: 'Tambahan', price: 5000,
    image: imgNasiDaunJeruk, imageAlt: 'Nasi daun jeruk' },
  { id: 'sambal-geprek', name: 'Sambal Geprek', category: 'Tambahan', price: 2000,
    image: imgSambalGeprek, imageAlt: 'Sambal geprek' },
  { id: 'sambal-ijo', name: 'Sambal Ijo', category: 'Tambahan', price: 2000,
    image: imgSambalIjo, imageAlt: 'Sambal ijo' },
  { id: 'saus-sachet', name: 'Saus Sachet', category: 'Tambahan', price: 2000,
    image: imgSausSachet, imageAlt: 'Saus sachet' },
]