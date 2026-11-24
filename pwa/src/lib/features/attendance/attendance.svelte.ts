import type { AttendanceDto, AttendanceStateDto } from '$lib/api/types';
import { current } from '$lib/auth/current.svelte';
import type { AppFailure } from '$lib/failure/failure';
import { failureText, REASON_KEY_REUSED } from '$lib/failure/failure';
import { minutesOfDay } from '$lib/format/datetime';
import { stampPhoto } from '$lib/platform/photo';
import { distanceMeters, readLocation, type LocationFix } from '$lib/platform/location';
import { permissions } from '$lib/platform/permissions.svelte';
import { t } from '$lib/text/t';
import { locationProblemText } from './location-problem';
import { stateOf, type AttendanceState, type ClockCelebration, type ClockKind } from './models';
import { stampLines } from './photo-stamp';

type ClockAttempt = { key: string; kind: ClockKind; scheduleId: string | null; photo: Blob; outside: boolean; note: string | null; fix: LocationFix; stamped: Blob };

const BASE = '/v2/attendance';
const PHOTO_NAME = 'attendance.jpg';
const LOCATION_INSIDE = 'inside';
const LOCATION_OUTSIDE = 'outside';

/** Keadaan layar Absen: status hari ini, lembar absen yang terbuka, dan perayaan setelah berhasil. */
export class AttendanceScreenState {
	state = $state<AttendanceState | null>(null);
	loading = $state(true);
	failure = $state<AppFailure | null>(null);
	/** Lembar absen yang sedang terbuka; null bila tertutup. */
	sheet = $state<ClockKind | null>(null);
	submitting = $state(false);
	submitError = $state<string | null>(null);
	/** Absen yang baru berhasil dan sedang dirayakan; lembar absen tetap terbuka di bawahnya sampai selesai. */
	celebration = $state<ClockCelebration | null>(null);
	acknowledging = $state(false);
	/** Jadwal yang baru dibuat lewat absen mandiri; absen datang memakainya. */
	selfScheduledId = $state<string | null>(null);
	/** Posisi yang dibaca saat lembar absen dibuka, untuk menampilkan jarak ke cabang sebelum memotret. */
	preview = $state<LocationFix | null>(null);
	/** Penyebab dan langkah perbaikan bila posisi gagal dibaca; null bila posisi terbaca atau belum dibaca. */
	locationProblem = $state<string | null>(null);
	locating = $state(false);

	private token = 0;
	/** Satu percobaan absen: kunci idempotensi beserta muatan yang persis sama dengan yang dikirim; dicoba lagi dengan muatan dan kunci yang sama, dan dibuang bila foto atau lokasi berganti. Hanya di memori halaman. */
	private attempt: ClockAttempt | null = null;

	constructor(private readonly onSessionExpired: () => void) {}

	/** Jarak posisi [preview] ke titik cabang; null bila salah satunya belum ada. */
	readonly previewDistance = $derived.by(() => {
		const fix = this.preview;
		const branch = this.state?.branch;
		if (!fix || !branch || branch.latitude === null || branch.longitude === null) return null;
		return distanceMeters(fix, branch.latitude, branch.longitude);
	});

	/** Dipanggil tiap halaman dibuka agar status selalu terbaru. */
	async load(): Promise<void> {
		const token = ++this.token;
		this.loading = this.state === null;
		this.failure = null;
		const result = await current.api().read<AttendanceStateDto>(`${BASE}/state`);
		if (token !== this.token) return;
		if (result.kind === 'unauthorized') return this.onSessionExpired();
		this.loading = false;
		if (result.kind === 'success') this.state = stateOf(result.value);
		else this.failure = result.failure;
	}

	openSheet(kind: ClockKind): void {
		this.attempt = null;
		this.sheet = kind;
		this.submitError = null;
		void this.locate();
	}

	/** Membaca posisi untuk pratinjau jarak; dipanggil saat lembar dibuka dan saat karyawan meminta baca ulang. */
	async locate(): Promise<void> {
		if (this.locating) return;
		this.locating = true;
		// Lokasi yang dibaca ulang membuat percobaan absen baru.
		this.attempt = null;
		this.locationProblem = null;
		const reading = await readLocation();
		permissions.observe(reading);
		this.preview =reading.kind === 'fix' ? reading.fix : null;
		this.locationProblem = locationProblemText(reading);
		this.locating = false;
	}

	closeSheet(): void {
		this.attempt = null;
		this.sheet = null;
		this.submitError = null;
		this.selfScheduledId = null;
		this.preview = null;
		this.locationProblem = null;
	}

	/** Setelah jadwal mandiri tersimpan, lembar absen datang langsung terbuka untuk jadwal itu. */
	startSelfScheduled(scheduleId: string): void {
		this.attempt = null;
		this.sheet = 'in';
		this.submitError = null;
		this.selfScheduledId = scheduleId;
		void this.load();
		void this.locate();
	}

	/** Membaca posisi lalu mengirim absen; foto dan keterangan datang dari lembar. */
	async submit(photo: Blob, outside: boolean, note: string, userName: string): Promise<void> {
		const kind = this.sheet;
		if (!kind || this.submitting) return;
		// Absen datang selalu menyebut jadwal yang tampil di layar; backend hanya memeriksanya, tidak memilihkan.
		const scheduleId = kind === 'in' ? (this.selfScheduledId ?? this.state?.schedule?.id ?? null) : null;
		if (kind === 'in' && scheduleId === null) return this.failSubmit(t('attendance_no_active_schedule'));

		this.submitting = true;
		this.submitError = null;
		const trimmedNote = note.trim() || null;
		// Percobaan ulang dengan foto dan keterangan yang sama mengirim muatan yang sama persis, tanpa membaca lokasi atau memotret lagi.
		let attempt = this.attempt;
		if (!attempt || attempt.kind !== kind || attempt.scheduleId !== scheduleId || attempt.photo !== photo || attempt.outside !== outside || attempt.note !== trimmedNote) {
			const reading = await readLocation();
			permissions.observe(reading);
			if (reading.kind !== 'fix') return this.failSubmit(locationProblemText(reading) ?? t('attendance_location_unavailable'));
			const fix = reading.fix;
			const lines = stampLines(userName, this.state?.branch ?? null, fix, outside, trimmedNote);
			// Cap gagal dibuat tidak menghalangi absen; foto dikirim apa adanya.
			const stamped = (await stampPhoto(photo, lines)) ?? photo;
			attempt = { key: crypto.randomUUID(), kind, scheduleId, photo, outside, note: trimmedNote, fix, stamped };
			this.attempt = attempt;
		}
		const { fix, stamped } = attempt;

		const form = new FormData();
		if (scheduleId) form.append('schedule_id', scheduleId);
		form.append('latitude', String(fix.latitude));
		form.append('longitude', String(fix.longitude));
		form.append('accuracy', String(fix.accuracyMeters));
		form.append('location_mode', outside ? LOCATION_OUTSIDE : LOCATION_INSIDE);
		if (trimmedNote) form.append('location_note', trimmedNote);
		form.append('photo', stamped, PHOTO_NAME);
		form.append('idempotency_key', attempt.key);

		const result = await current.api().write<AttendanceDto>('POST', `${BASE}/${kind === 'in' ? 'clock-in' : 'clock-out'}`, form);
		if (result.kind === 'success') {
			this.attempt = null;
			return this.celebrate(kind);
		}
		if (result.kind === 'unauthorized') return this.onSessionExpired();
		if (result.failure.kind === 'rejected' && result.failure.reason === REASON_KEY_REUSED) this.attempt = null;
		this.failSubmit(failureText(result.failure));
		void this.load();
	}

	/** Menutup perayaan beserta lembar absen di bawahnya, lalu memuat ulang status. */
	finishCelebration(): void {
		this.attempt = null;
		this.celebration = null;
		this.sheet = null;
		this.submitting = false;
		this.selfScheduledId = null;
		this.preview = null;
		this.locationProblem = null;
		void this.load();
	}

	/** Memuat status terbaru agar jam yang dirayakan sama dengan yang tercatat di server. */
	private async celebrate(kind: ClockKind): Promise<void> {
		const result = await current.api().read<AttendanceStateDto>(`${BASE}/state`);
		const fresh = result.kind === 'success' ? stateOf(result.value) : null;
		const record = fresh?.record ?? null;
		const minutes = kind === 'in' ? (record?.clockIn ? minutesOfDay(record.clockIn.time) : null) : (record?.workMinutes ?? null);
		if (fresh) this.state = fresh;
		this.celebration = { kind, minutes };
	}

	/** Menandai semua pemberitahuan yang tampil sudah dilihat, lalu memuat ulang. */
	async acknowledgeNotices(): Promise<void> {
		const ids = this.state?.notices.map((notice) => notice.id) ?? [];
		if (ids.length === 0 || this.acknowledging) return;
		this.acknowledging = true;
		const result = await current.api().write('POST', `${BASE}/auto-close-notices/ack`, { ids });
		if (result.kind === 'unauthorized') return this.onSessionExpired();
		this.acknowledging = false;
		if (result.kind === 'success' && this.state) {
			// Pemberitahuan langsung disembunyikan agar tombolnya tidak bisa diketuk lagi selama memuat ulang.
			this.state = { ...this.state, notices: [] };
			void this.load();
		}
	}

	private failSubmit(text: string): void {
		this.submitting = false;
		this.submitError = text;
	}
}
