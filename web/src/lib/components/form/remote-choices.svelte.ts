import { userMessage } from '$lib/api/user-message';
import { errorText } from '$lib/text/errors';

// Jeda ketik sebelum bertanya ke server (rules 6.19 butir 12).
const SEARCH_DELAY_MS = 250;
// Sama dengan Loadable di app, supaya kerangka tidak berkedip saat server menjawab sangat cepat.
const MIN_SEARCH_SHOWN_MS = 350;

/** Satu halaman pilihan; `next` kosong berarti daftar sudah habis, selain itu diteruskan apa adanya untuk halaman berikutnya. */
export type ChoicePage<T> = { items: T[]; next: string | null };

type Fetch<T> = (query: string, next: string | null) => Promise<ChoicePage<T>>;

/** Penyesuai untuk sumber bernomor halaman (mulai 1): halaman yang lebih pendek dari `size` berarti akhir daftar. */
export function byPage<T>(size: number, fetch: (query: string, page: number) => Promise<T[]>): Fetch<T> {
	return async (query, next) => {
		const page = next === null ? 1 : Number(next);
		const items = await fetch(query, page);
		return { items, next: items.length === size ? String(page + 1) : null };
	};
}

/** Pilihan yang dicari di server dan dimuat per halaman saat daftar digulir, sehingga tidak ada pilihan yang terpotong berapa pun jumlahnya. */
export class RemoteChoices<T> {
	items = $state<T[]>([]);
	/** Pesan gagal muat dari pintu galat; kosong berarti tidak ada masalah. */
	problem = $state('');
	/** Halaman pertama sedang dicari, termasuk selama jeda ketik; daftar diganti kerangka. */
	searching = $state(true);
	/** Halaman berikutnya sedang dimuat; daftar tetap, kerangka di ujung bawah. */
	loadingMore = $state(false);
	/** Kata cari yang sedang berlaku; kosong berarti daftar awal tanpa cari. */
	typed = $state('');

	#fetch: Fetch<T>;
	#key: (item: T) => string;
	#query: string | null = null;
	#next: string | null = null;
	#run = 0;
	#timer: ReturnType<typeof setTimeout> | undefined;

	constructor(fetch: Fetch<T>, key: (item: T) => string) {
		this.#fetch = fetch;
		this.#key = key;
	}

	search(text: string): void {
		const query = text.trim();
		if (query === this.#query) return;
		this.#query = query;
		this.typed = query;
		clearTimeout(this.#timer);
		const run = ++this.#run;
		this.searching = true;
		this.loadingMore = false;
		const started = performance.now();
		const load = () => void this.#load(run, query, null, started);
		if (query === '') load();
		else this.#timer = setTimeout(load, SEARCH_DELAY_MS);
	}

	more(): void {
		if (this.#query === null || this.#next === null || this.searching || this.loadingMore) return;
		this.loadingMore = true;
		void this.#load(this.#run, this.#query, this.#next, performance.now());
	}

	/** Memuat ulang kata cari yang sama dari halaman pertama, misalnya setelah rentang tanggal berganti. */
	refresh(): void {
		const query = this.#query ?? '';
		this.#query = null;
		this.search(query);
	}

	/** Mulai lagi dari awal tanpa kata cari, misalnya setelah cabang berganti. */
	reset(): void {
		clearTimeout(this.#timer);
		this.#run++;
		this.#query = null;
		this.items = [];
		this.problem = '';
		this.search('');
	}

	async #load(run: number, query: string, next: string | null, started: number): Promise<void> {
		const first = next === null;
		try {
			const found = await this.#fetch(query, next);
			const remaining = first ? MIN_SEARCH_SHOWN_MS - (performance.now() - started) : 0;
			if (remaining > 0) await new Promise((resolve) => setTimeout(resolve, remaining));
			if (run !== this.#run) return;
			const merged = first ? found.items : [...this.items, ...found.items];
			// Data bisa bergeser di antara dua halaman, jadi pilihan yang sudah tampil tidak diulang.
			this.items = [...new Map(merged.map((item) => [this.#key(item), item] as const)).values()];
			this.#next = found.next;
			this.problem = '';
		} catch (failure) {
			if (run === this.#run) this.problem = userMessage(failure, errorText.unknown);
		} finally {
			if (run === this.#run) {
				if (first) this.searching = false;
				else this.loadingMore = false;
			}
		}
	}
}
