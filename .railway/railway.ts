// Susunan proyek Railway klien ini: empat layanan (situs publik, backend, web admin, PWA), Postgres, Redis, dan bucket, sudah saling tersambung.
import { bucket, defineRailway, github, postgres, project, redis, preserve, service } from "railway/iac";

const REPOSITORY = "NganjukBersatu/iwa-geprek";
// Port tetap supaya web dan PWA bisa menyebut alamat privat backend tanpa menebak.
const BACKEND_PORT = "8000";
const BACKEND_URL = "http://${{backend.RAILWAY_PRIVATE_DOMAIN}}:${{backend.PORT}}";
// Railway mengakhiri TLS di tepi, jadi skema dan host asli dibaca dari header yang diteruskannya.
// Proses yang jatuh dinyalakan lagi, paling banyak tiga kali, supaya kerusakan tetap tidak berputar tanpa akhir.
const RESTART = { restartPolicyType: "ON_FAILURE", restartPolicyMaxRetries: 3 } as const;
const NODE_SERVER = { NODE_ENV: "production", HOST: "0.0.0.0", PROTOCOL_HEADER: "x-forwarded-proto", HOST_HEADER: "x-forwarded-host" };

export default defineRailway(() => {
  const database = postgres("postgres");
  const cache = redis("redis");
  const files = bucket("files", { region: "sin" });

  const backend = service("backend", {
    source: github(REPOSITORY, { rootDirectory: "backend" }),
    // Mendengarkan di :: supaya terjangkau dari jaringan privat Railway, tempat web dan PWA memanggilnya.
    start: "uvicorn server:app --host :: --port $PORT --proxy-headers --forwarded-allow-ips='*'",
    // Migrasi dan penjaga data berjalan sebelum versi baru menerima permintaan; gagal berarti deploy dihentikan.
    preDeploy: "python scripts/pra_deploy.py",
    healthcheck: "/health",
    healthcheckTimeout: 300,
    deploy: RESTART,
    env: {
      PORT: BACKEND_PORT,
      DATABASE_URL: database.env.DATABASE_URL,
      REDIS_URL: cache.env.REDIS_URL,
      PUBLIC_URL: "https://${{RAILWAY_PUBLIC_DOMAIN}}",
      // Rahasia tidak ditulis di repositori; nilainya diisi sekali di Railway dan dipertahankan di sini.
      JWT_SECRET_KEY: preserve(),
      // Bucket tidak punya pengakses env di DSL, jadi variabelnya dirujuk dengan sintaks rujukan Railway.
      BUCKET: "${{files.BUCKET}}",
      ENDPOINT: "${{files.ENDPOINT}}",
      ACCESS_KEY_ID: "${{files.ACCESS_KEY_ID}}",
      SECRET_ACCESS_KEY: "${{files.SECRET_ACCESS_KEY}}",
      REGION: "${{files.REGION}}",
      // Aplikasi di bawah versi ini diminta memperbarui lewat halaman unduhan web admin; naikkan bersama versi rilis.
      MIN_VERSION_APK: "1.0.0",
      MIN_VERSION_PWA: "1.0.0",
      DOWNLOAD_URL: "https://${{web.RAILWAY_PUBLIC_DOMAIN}}/unduh",
    },
  });

  const web = service("web", {
    source: github(REPOSITORY, { rootDirectory: "web" }),
    build: "npm run build",
    start: "node build",
    deploy: RESTART,
    env: { ...NODE_SERVER, BACKEND_URL, PUBLIC_PWA_URL: "https://${{pwa.RAILWAY_PUBLIC_DOMAIN}}" },
  });

  const pwa = service("pwa", {
    source: github(REPOSITORY, { rootDirectory: "pwa" }),
    build: "npm run build",
    start: "node build",
    healthcheck: "/health",
    healthcheckTimeout: 120,
    deploy: RESTART,
    // Foto absen dikirim lewat server ini, jadi batas isi permintaan dinaikkan.
    env: { ...NODE_SERVER, BACKEND_URL, BODY_SIZE_LIMIT: "100M" },
  });

  // Situs publik Vue, layanan iwa-geprek yang sudah ada di proyek Railway: Railpack mengenali Vite, membangun ke dist, lalu menyajikannya dengan Caddy sebagai SPA; tidak butuh perintah start.
  const site = service("iwa-geprek", {
    source: github(REPOSITORY, { rootDirectory: "site" }),
    build: "npm run build",
    deploy: RESTART,
    // Dibaca Vite saat build: tombol di bagian unduhan membuka halaman Unduhan web admin.
    env: { VITE_DOWNLOAD_PAGE_URL: "https://${{web.RAILWAY_PUBLIC_DOMAIN}}/unduh" },
  });

  return project("iwageprek", {
    resources: [database, cache, files, backend, web, pwa, site],
  });
});
