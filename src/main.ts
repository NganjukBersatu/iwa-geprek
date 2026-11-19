import { createApp } from 'vue'

// Font Poppins di-host lokal lewat npm (@fontsource) — tanpa Google Fonts / CDN.
import '@fontsource/poppins/latin-400.css'
import '@fontsource/poppins/latin-500.css'
import '@fontsource/poppins/latin-500-italic.css'
import '@fontsource/poppins/latin-600.css'
import '@fontsource/poppins/latin-700.css'
import '@fontsource/poppins/latin-800.css'
import '@fontsource/poppins/latin-800-italic.css'

import './assets/css/main.css'
import './assets/css/base.css'

import App from './App.vue'
import router from './router'

createApp(App).use(router).mount('#app')