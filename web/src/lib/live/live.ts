import { browser } from '$app/environment';
import { get, writable } from 'svelte/store';
import { isSignedIn } from '$lib/auth/session';
import { selectedBranch } from '$lib/stores/branch';

const STREAM_PATH = '/api/web/management/live';
// Satu nama untuk kunci pemimpin dan saluran antartab, supaya semua tab berbagi satu koneksi.
const SHARED_NAME = 'management-web-live';
const DEBOUNCE_MILLISECONDS = 250;
// Server berdetak tiap 3 detik; selama ini tanpa detak berarti koneksi mati diam-diam.
const SILENCE_MILLISECONDS = 10_000;

// Jeda antarpercobaan berlipat dari dasar sampai plafon dengan separuh acak supaya banyak tab tidak kembali bersamaan; setelah percobaan terakhir menunggu orang.
const RETRY_BASE_MILLISECONDS = 1000;
const RETRY_CEILING_MILLISECONDS = 30_000;
const MAX_ATTEMPTS = 8;

type Change = { tables: string[]; outlets: string[] };
/** Sinyal antartab tanpa data: diteruskan pemegang koneksi, kecuali `retry` yang diminta tab lain kepadanya. */
type Signal =
	| { kind: 'beat' }
	| { kind: 'all' }
	| { kind: 'change'; change: Change }
	| { kind: 'state'; connected: boolean; gaveUp: boolean }
	| { kind: 'retry' };

/** Salah selama aliran putus dan sedang disambung ulang; kerangka aplikasi menampilkan bilah untuknya. */
export const liveConnected = writable(true);
/** Benar setelah percobaan otomatis habis; bilah lalu menawarkan tombol, bukan menjanjikan coba ulang. */
export const liveGaveUp = writable(false);
type Listener = { tables: Set<string>; run: () => void; timer?: ReturnType<typeof setTimeout> };

const sharable = (): boolean => browser && 'locks' in navigator && typeof BroadcastChannel !== 'undefined';

/**
 * Satu pintu data live untuk seluruh peramban: halaman menyebut tabel yang ditampilkannya dan apa yang dilakukan saat tabel itu berubah.
 * Tab pemegang kunci membuka satu koneksi dan meneruskan sinyalnya, karena peramban hanya mengizinkan enam koneksi per host.
 * Server hanya mengirim sinyal, tidak pernah data, jadi `run` memuat ulang lewat rute biasa dengan tenang (tanpa meredupkan atau mengosongkan).
 *
 *   onMount(() => live.on(['expenses', 'cash_sessions'], () => state.refresh()));
 */
class Live {
	private listeners = new Set<Listener>();
	private source: EventSource | null = null;
	private watchdog: ReturnType<typeof setTimeout> | undefined;
	private retryTimer: ReturnType<typeof setTimeout> | undefined;
	private attempts = 0;
	private dropped = false;
	private channel: BroadcastChannel | null = null;
	private leading = false;
	private followed = false;
	private release: (() => void) | null = null;
	private waiting: AbortController | null = null;

	on(tables: string[], run: () => void): () => void {
		const listener: Listener = { tables: new Set(tables), run };
		this.listeners.add(listener);
		this.start();
		return () => {
			clearTimeout(listener.timer);
			this.listeners.delete(listener);
			if (this.listeners.size === 0) this.stop();
		};
	}

	/** Membuka koneksi lagi seketika bila masih ada yang mendengarkan, dengan jatah percobaan otomatis yang baru. */
	reconnect(): void {
		if (this.listeners.size === 0) return;
		if (sharable() && !this.leading) {
			// Tab pengikut tidak memegang koneksi, jadi meminta pemimpin; bila belum ada pemimpin, tab ini ikut mengantre kunci.
			this.channel?.postMessage({ kind: 'retry' } satisfies Signal);
			this.start();
			return;
		}
		this.retryNow();
	}

	private retryNow(): void {
		clearTimeout(this.retryTimer);
		this.attempts = 0;
		this.publishState(get(liveConnected), false);
		this.connect();
	}

	private start(): void {
		if (!browser || !isSignedIn()) return;
		if (!sharable()) {
			this.connect();
			return;
		}
		if (!this.channel) {
			this.channel = new BroadcastChannel(SHARED_NAME);
			this.channel.onmessage = (event: MessageEvent<Signal>) => this.receive(event.data);
		}
		if (this.leading || this.waiting) return;
		const waiting = new AbortController();
		this.waiting = waiting;
		navigator.locks
			.request(SHARED_NAME, { signal: waiting.signal }, () => {
				this.waiting = null;
				this.leading = true;
				// Tab yang tadinya hanya menerima bisa melewatkan sinyal saat pemimpin lama ditutup, jadi koneksi pertamanya dianggap menyusul.
				this.dropped = this.followed;
				this.connect();
				return new Promise<void>((resolve) => (this.release = resolve));
			})
			.catch((error: unknown) => {
				// Dibatalkan sendiri lewat stop(); kegagalan lain dibiarkan naik.
				if (!(error instanceof DOMException && error.name === 'AbortError')) throw error;
			});
	}

	private stop(): void {
		this.waiting?.abort();
		this.waiting = null;
		this.disconnect();
		this.leading = false;
		this.release?.();
		this.release = null;
		this.channel?.close();
		this.channel = null;
	}

	private connect(): void {
		if (!browser || this.source || !isSignedIn()) return;
		// Sesi masuk ikut lewat cookie yang dikirim peramban sendiri, jadi tidak ada token di alamat.
		const source = new EventSource(STREAM_PATH);
		this.source = source;
		this.beat();
		let greeted = false;
		source.addEventListener('resync', () => {
			// Resync pertama hanya salam kecuali setelah putus; resync berikutnya berarti server tidak sempat menyimpan semua sinyal untuk layar ini.
			if (this.dropped || greeted) this.emit({ kind: 'all' });
			greeted = true;
			this.dropped = false;
			this.attempts = 0;
			this.publishState(true, false);
		});
		source.addEventListener('detak', () => this.emit({ kind: 'beat' }));
		source.addEventListener('ubah', (event) => {
			const change = JSON.parse((event as MessageEvent<string>).data) as Change;
			this.emit({ kind: 'change', change });
		});
		source.onerror = () => {
			this.dropped = true;
			// Penolakan (sesi habis) menutup koneksi untuk seterusnya; koneksi yang hilang disambung ulang oleh kita dengan jeda, bukan oleh peramban.
			if (source.readyState === EventSource.CLOSED) {
				this.publishState(true, false);
				this.disconnect();
				return;
			}
			this.lose();
		};
	}

	/** Koneksi mati: tutup, tampilkan bilah, lalu coba lagi nanti. */
	private lose(): void {
		this.dropped = true;
		this.closeSource();
		if (this.listeners.size === 0) {
			this.publishState(false, false);
			return;
		}
		if (this.attempts >= MAX_ATTEMPTS) {
			this.publishState(false, true);
			return;
		}
		this.publishState(false, false);
		const ceiling = Math.min(RETRY_CEILING_MILLISECONDS, RETRY_BASE_MILLISECONDS * 2 ** this.attempts);
		this.attempts += 1;
		clearTimeout(this.retryTimer);
		this.retryTimer = setTimeout(() => this.connect(), ceiling / 2 + Math.random() * (ceiling / 2));
	}

	private closeSource(): void {
		clearTimeout(this.watchdog);
		this.source?.close();
		this.source = null;
	}

	private disconnect(): void {
		clearTimeout(this.retryTimer);
		this.attempts = 0;
		liveGaveUp.set(false);
		if (this.listeners.size === 0) liveConnected.set(true);
		this.closeSource();
	}

	/** Menyetel keadaan koneksi di tab ini lalu meneruskannya ke tab lain. */
	private publishState(connected: boolean, gaveUp: boolean): void {
		this.emit({ kind: 'state', connected, gaveUp });
	}

	/** Menerapkan sinyal di tab ini lalu meneruskannya ke tab lain. */
	private emit(signal: Signal): void {
		this.apply(signal);
		this.channel?.postMessage(signal);
	}

	/** Sinyal dari tab lain: permintaan coba ulang hanya dijawab pemimpin, sisanya diterapkan sebagai pengikut. */
	private receive(signal: Signal): void {
		if (signal.kind === 'retry') {
			if (this.leading) this.retryNow();
			return;
		}
		this.followed = true;
		this.apply(signal);
	}

	private apply(signal: Signal): void {
		switch (signal.kind) {
			case 'beat':
				this.beat();
				// Detak berarti aliran hidup; tab pengikut yang sempat menandai putus kembali tersambung.
				liveConnected.set(true);
				return;
			case 'all':
				this.fire(() => true);
				return;
			case 'state':
				liveConnected.set(signal.connected);
				liveGaveUp.set(signal.gaveUp);
				return;
			case 'change': {
				this.beat();
				const branch = get(selectedBranch);
				if (branch && signal.change.outlets.length > 0 && !signal.change.outlets.includes(branch)) return;
				const touched = new Set(signal.change.tables);
				this.fire((listener) => [...listener.tables].some((table) => touched.has(table)));
				return;
			}
			case 'retry':
				return;
			default:
				return;
		}
	}

	private beat(): void {
		clearTimeout(this.watchdog);
		this.watchdog = setTimeout(() => {
			this.dropped = true;
			// Hanya pemegang koneksi yang menyambung ulang; tab pengikut menandai putus dan menunggu sinyal pemimpin.
			if (sharable() && !this.leading) {
				liveConnected.set(false);
				return;
			}
			this.lose();
		}, SILENCE_MILLISECONDS);
	}

	/** Beberapa sinyal beruntun (satu simpan menyentuh banyak tabel) menjadi satu muat ulang per pendengar. */
	private fire(wanted: (listener: Listener) => boolean): void {
		for (const listener of this.listeners) {
			if (!wanted(listener)) continue;
			clearTimeout(listener.timer);
			listener.timer = setTimeout(listener.run, DEBOUNCE_MILLISECONDS);
		}
	}
}

export const live = new Live();

if (browser) {
	// Kembali daring atau kembali ke tab setelah koneksi tertutup: sambung ulang sekali, lalu resync menyusul.
	const reopen = () => {
		if (document.visibilityState === 'visible') live.reconnect();
	};
	document.addEventListener('visibilitychange', reopen);
	window.addEventListener('online', reopen);
}
