import { browser } from '$app/environment';
import { cameraProblemOf, type CameraProblem } from './camera';
import { probeLocationService, readLocation, type LocationReading } from './location';
import { reportPermissionFailure } from './permission-report';

/** Urutan = urutan baris di gerbang. */
export const PERMISSION_KINDS = ['location', 'camera', 'gps'] as const;
export type PermissionKind = (typeof PERMISSION_KINDS)[number];
export type PermissionStatus = 'granted' | 'denied';

/** Sebab sebuah izin belum ada; null berarti belum pernah dicoba atau sudah terpenuhi. */
export type PermissionReason = 'denied' | 'timeout' | 'serviceOff' | 'unanswered' | CameraProblem;

const CAMERA_KEY = 'employee.camera-allowed';
const LOCATION_KEY = 'employee.location-allowed';
const GPS_KEY = 'employee.gps-on';

/** Browser tidak menghitung waktu menunggu kotak izin, jadi tanpa batas ini jawaban yang tidak datang mengunci tombol selamanya. */
const STAGE_DEADLINE_MILLIS = 15_000;
/** Pertanyaan status ke browser yang tidak dijawab dianggap tidak didukung, supaya gerbang tidak tertahan di "belum dibaca". */
const QUERY_DEADLINE_MILLIS = 2_000;
/** Kegagalan yang sama dilaporkan paling cepat sekali per jeda ini. */
const REPORT_INTERVAL_MILLIS = 30_000;
const REFERENCE_LENGTH = 6;
/** Tanpa huruf dan angka yang mudah tertukar (0, O, 1, I). */
const REFERENCE_ALPHABET = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';

function remembered(key: string): boolean {
	try {
		return localStorage.getItem(key) === '1';
	} catch {
		return false;
	}
}

function remember(key: string, value: boolean): void {
	try {
		if (value) localStorage.setItem(key, '1');
		else localStorage.removeItem(key);
	} catch {
		// Penyimpanan diblokir: status dibaca ulang dari izin browser.
	}
}

/** Jawaban izin dari browser; null bila tidak didukung, gagal, atau tidak menjawab dalam [QUERY_DEADLINE_MILLIS]. */
async function queried(name: 'geolocation' | 'camera'): Promise<PermissionState | null> {
	const silence = new Promise<null>((resolve) => setTimeout(() => resolve(null), QUERY_DEADLINE_MILLIS));
	try {
		const answer = navigator.permissions.query({ name: name as PermissionName }).then((result) => result.state);
		return await Promise.race([answer, silence]);
	} catch {
		return null;
	}
}

function newReference(): string {
	const bytes = crypto.getRandomValues(new Uint8Array(REFERENCE_LENGTH));
	return Array.from(bytes, (byte) => REFERENCE_ALPHABET[byte % REFERENCE_ALPHABET.length]).join('');
}

/** Izin dan layanan perangkat yang dibutuhkan absen: lokasi, kamera, dan GPS yang menyala. */
class DevicePermissions {
	status = $state<Record<PermissionKind, PermissionStatus>>({ location: 'denied', camera: 'denied', gps: 'denied' });
	/** Benar setelah status pertama selesai dibaca, sebelum itu gerbang izin belum boleh tampil. */
	loaded = $state(false);
	/** Benar selama permintaan izin berjalan, supaya tombol menampilkan keadaan memuat. */
	checking = $state(false);
	/** Sebab izin belum ada setelah dicoba, supaya pengguna tahu langkahnya. */
	reason = $state<Record<PermissionKind, PermissionReason | null>>({ location: null, camera: null, gps: null });
	/** Kode pendek yang sama dengan yang tercatat di server, kosong sampai ada kegagalan; dibacakan ke admin bila tetap gagal. */
	reference = $state('');

	/** Nomor permintaan terakhir; hasil permintaan yang sudah dilepas tidak boleh menimpa sebabnya. */
	private generation = 0;
	private lastReported = new Map<string, number>();

	constructor() {
		if (!browser) return;
		void this.refresh();
		document.addEventListener('visibilitychange', () => {
			if (document.visibilityState !== 'visible') return;
			this.release();
			void this.refresh();
		});
	}

	/** Membaca ulang status, misalnya saat app kembali aktif. */
	async refresh(): Promise<void> {
		try {
			const location = await queried('geolocation');
			const camera = await queried('camera');
			// Safari iPhone bisa menjawab "prompt" walau izin sudah diberikan, jadi hanya "denied" yang membatalkan bukti bacaan berhasil.
			const locationGranted = location === 'denied' ? false : location === 'granted' ? true : remembered(LOCATION_KEY);
			if (location === 'denied') {
				remember(LOCATION_KEY, false);
				remember(GPS_KEY, false);
			}
			// Browser tidak menyebut layanan lokasi mati; dipastikan dengan bacaan lama yang murah, hanya bila izin sudah pasti ada agar tidak memunculkan kotak izin.
			if (location === 'granted') {
				const on = await probeLocationService();
				if (on !== null) remember(GPS_KEY, on);
			}
			const cameraGranted = camera === 'denied' ? false : camera === 'granted' ? true : remembered(CAMERA_KEY);
			this.status = {
				location: locationGranted ? 'granted' : 'denied',
				camera: cameraGranted ? 'granted' : 'denied',
				gps: locationGranted && remembered(GPS_KEY) ? 'granted' : 'denied'
			};
			const open = (kind: PermissionKind) => (this.status[kind] === 'granted' ? null : this.reason[kind]);
			this.reason = { location: open('location'), camera: open('camera'), gps: open('gps') };
		} finally {
			// Gerbang tidak boleh tertahan di "belum dibaca" walau pembacaan gagal.
			this.loaded = true;
		}
	}

	/** Meminta izin untuk [kinds]; lokasi dan GPS berbagi satu bacaan sehingga kotak izin sistem muncul sekali. */
	async request(kinds: readonly PermissionKind[]): Promise<void> {
		if (this.checking) return;
		this.checking = true;
		const run = ++this.generation;
		const started = performance.now();
		try {
			if (kinds.includes('camera') && this.status.camera !== 'granted') await this.stage(run, ['camera'], () => this.requestCamera(run));
			if (run !== this.generation) return;
			const wantsLocation = kinds.includes('location') || kinds.includes('gps');
			if (wantsLocation && (this.status.location !== 'granted' || this.status.gps !== 'granted')) {
				await this.stage(run, ['location', 'gps'], async () => this.applyReading(await readLocation(), run));
			}
			await this.refresh();
			if (run === this.generation) this.reportFailures(kinds, Math.round(performance.now() - started));
		} finally {
			if (run === this.generation) this.checking = false;
		}
	}

	/** Mencatat bacaan lokasi dari layar lain (absen) agar gerbang izin ikut benar; bacaan lambat atau sesaat tidak mengubah apa pun. */
	observe(reading: LocationReading): void {
		if (reading.kind === 'fix') {
			remember(LOCATION_KEY, true);
			remember(GPS_KEY, true);
		} else if (reading.kind === 'denied') {
			remember(LOCATION_KEY, false);
			remember(GPS_KEY, false);
		} else {
			return;
		}
		void this.refresh();
	}

	/** Melepas permintaan yang masih menggantung; jawabannya, bila datang kemudian, tetap dicatat sebagai fakta. */
	private release(): void {
		if (!this.checking) return;
		this.generation++;
		this.checking = false;
	}

	/** Satu tahap permintaan dengan batas waktunya sendiri, supaya satu izin yang macet tidak menahan izin berikutnya. */
	private async stage(run: number, kinds: readonly PermissionKind[], work: () => Promise<void>): Promise<void> {
		let timer: ReturnType<typeof setTimeout> | undefined;
		const silence = new Promise<'expired'>((resolve) => {
			timer = setTimeout(() => resolve('expired'), STAGE_DEADLINE_MILLIS);
		});
		const done = work().then(() => 'done' as const);
		const outcome = await Promise.race([done, silence]);
		clearTimeout(timer);
		if (outcome === 'done') return;
		if (run === this.generation) this.markUnanswered(kinds);
		// Jawaban yang datang terlambat tetap dicatat sebagai fakta, lalu status dibaca ulang.
		void done.then(() => this.refresh());
	}

	private async requestCamera(run: number): Promise<void> {
		try {
			const stream = await navigator.mediaDevices.getUserMedia({ video: true });
			stream.getTracks().forEach((track) => track.stop());
			remember(CAMERA_KEY, true);
			if (run === this.generation) this.reason = { ...this.reason, camera: null };
		} catch (error) {
			remember(CAMERA_KEY, false);
			if (run === this.generation) this.reason = { ...this.reason, camera: cameraProblemOf(error) };
		}
	}

	private applyReading(reading: LocationReading, run: number): void {
		remember(LOCATION_KEY, reading.kind !== 'denied');
		remember(GPS_KEY, reading.kind === 'fix');
		if (run !== this.generation) return;
		const gps: PermissionReason | null = reading.kind === 'timeout' ? 'timeout' : reading.kind === 'unavailable' ? 'serviceOff' : null;
		this.reason = { ...this.reason, location: reading.kind === 'denied' ? 'denied' : null, gps };
	}

	private markUnanswered(kinds: readonly PermissionKind[]): void {
		const next = { ...this.reason };
		for (const kind of kinds) if (this.status[kind] !== 'granted') next[kind] = 'unanswered';
		this.reason = next;
	}

	/** Setiap izin yang tetap belum ada beserta sebabnya dikirim ke log server, dengan kode rujukan yang sama dengan yang tampil di gerbang. */
	private reportFailures(kinds: readonly PermissionKind[], elapsedMillis: number): void {
		for (const kind of kinds) {
			const reason = this.reason[kind];
			if (this.status[kind] === 'granted' || reason === null) continue;
			const key = `${kind}:${reason}`;
			const now = performance.now();
			if (now - (this.lastReported.get(key) ?? -REPORT_INTERVAL_MILLIS) < REPORT_INTERVAL_MILLIS) continue;
			this.lastReported.set(key, now);
			if (this.reference === '') this.reference = newReference();
			void reportPermissionFailure({ kind, reason, elapsedMillis, reference: this.reference });
		}
	}
}

export const permissions = new DevicePermissions();
