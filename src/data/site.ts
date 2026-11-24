import { Instagram, MessageCircle } from 'lucide-vue-next'

export type NavKey = 'beranda' | 'keunggulan' | 'menu' | 'kontak' | 'karier'

export const navLinks: { key: NavKey; label: string; to: string }[] = [
  { key: 'beranda', label: 'Beranda', to: '/#beranda' },
  { key: 'keunggulan', label: 'Keunggulan', to: '/#keunggulan' },
  { key: 'menu', label: 'Menu', to: '/menu' },
  { key: 'kontak', label: 'Kontak', to: '/#kontak' },
  { key: 'karier', label: 'Karier', to: '/#karier' },
]


const WHATSAPP_NUMBER = '6285736882888'

export const business = {
  name: 'IWAGEPREK',
  tagline: 'IKAN GEPREK KHAS',
  phoneDisplay: '0857 3688 2888',
  phoneHref: 'tel:+6285736882888',
  whatsappUrl: `https://wa.me/${WHATSAPP_NUMBER}`,
  email: 'hi.iwageprek@gmail.com',
  address: 'Kertosono, Nganjuk',
  hours: '10.00 – 22.00 WIB',
  instagramHandle: '@iwageprek',
  instagramUrl: 'https://instagram.com/iwageprek',
  mapsUrl:
    'https://www.google.com/maps/place/IWAGEPREK+-+Ikan+Geprek+Crispy/@-7.5888873,112.0956103,45a,75y,330.88h,86.29t/data=!3m7!1e1!3m5!1sRKomq9Kc_A5G-shTFL5VmA!2e0!6shttps:%2F%2Fstreetviewpixels-pa.clients6.google.com%2Fv1%2Fthumbnail%3Fcb_client%3Dmaps_sv.tactile%26w%3D900%26h%3D600%26pitch%3D3.706933840966812%26panoid%3DRKomq9Kc_A5G-shTFL5VmA%26yaw%3D330.88361027238494!7i16384!8i8192!4m14!1m7!3m6!1s0x2e7847cd48f94f09:0x7515abdf2b2ef0bb!2sIWAGEPREK+-+Ikan+Geprek+Crispy!8m2!3d-7.5888233!4d112.095582!16s%2Fg%2F11z_fhdjls!3m5!1s0x2e7847cd48f94f09:0x7515abdf2b2ef0bb!8m2!3d-7.5888233!4d112.095582!16s%2Fg%2F11z_fhdjls?entry=ttu&g_ep=EgoyMDI2MTExNi4wIKXMDSoASAFQAw%3D%3D',
  footerText:
    'Ikan segar pilihan dengan sambal geprek khas yang menggugah selera. Nikmati hidangan lezat bersama keluarga.',
  copyright: '© 2026 IWAGEPREK. Seluruh hak cipta dilindungi.',
}

export const socialLinks = [
  { label: 'Instagram', url: business.instagramUrl, icon: Instagram },
  { label: 'WhatsApp', url: business.whatsappUrl, icon: MessageCircle },
]