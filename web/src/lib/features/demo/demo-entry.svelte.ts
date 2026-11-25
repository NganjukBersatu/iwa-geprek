import { goto } from '$app/navigation';
import { api } from '$lib/api';
import { ApiError } from '$lib/api/http';
import type { DemoStage, DemoStatus } from '$lib/api/types';
import { userMessage } from '$lib/api/user-message';
import { mayEnterWeb, saveSession } from '$lib/auth/session';
import { PAGES } from '$lib/nav/pages';
import { demoMode } from '$lib/stores/demo-mode.svelte';
import { authText } from '$lib/text/auth';
import { demoText } from '$lib/text/demo';

/** Langkah yang tampil di layar memuat, urut seperti langkah server. */
export const DEMO_STEPS = ['preparing', 'loading', 'linking', 'ready'] as const;
export type DemoStep = (typeof DEMO_STEPS)[number];
export type StepState = 'done' | 'current' | 'pending';

const POLL_MILLIS = 700;
// Setiap langkah tampil paling sedikit selama ini, supaya kemajuan terasa mulus walau server lebih cepat.
const STEP_MIN_MILLIS = 1000;
// Batas tunggu seluruh penyiapan; lewat dari ini layar berhenti dan menawarkan coba lagi.
const MAX_WAIT_MILLIS = 180_000;
// Kegagalan jaringan beruntun yang masih ditoleransi saat memantau.
const MAX_POLL_FAILURES = 5;
const READY_INDEX = DEMO_STEPS.indexOf('ready');

function stepIndex(stage: DemoStage): number {
	const index = DEMO_STEPS.indexOf(stage as DemoStep);
	return index < 0 ? -1 : index;
}

const pause = (millis: number) => new Promise<void>((resolve) => setTimeout(resolve, millis));

/** Masuk ke mode demo dari halaman masuk: mulai menyiapkan, memantau langkah server, lalu masuk sebagai pemilik demo. */
export class DemoEntryState {
	available = $state(false);
	/** Layar memuat tampil sejak tombol ditekan sampai pindah halaman atau dibatalkan. */
	running = $state(false);
	/** Langkah yang sedang tampil; naik paling cepat satu langkah per STEP_MIN_MILLIS. */
	shown = $state(0);
	error = $state('');
	#serverIndex = 0;
	#serverPercent = 0;
	#run = 0;

	/** Persen bilah langkah memuat: mengikuti server selama langkah itu tampil, penuh setelah dilewati. */
	get percent(): number {
		const loading = DEMO_STEPS.indexOf('loading');
		if (this.shown < loading) return 0;
		if (this.shown > loading || this.#serverIndex > loading) return 100;
		return Math.max(0, Math.min(100, Math.round(this.#serverPercent)));
	}

	stateOf(step: DemoStep): StepState {
		const index = DEMO_STEPS.indexOf(step);
		if (index < this.shown || (index === READY_INDEX && this.shown === READY_INDEX)) return 'done';
		return index === this.shown ? 'current' : 'pending';
	}

	/** Tombol hanya tampil bila server punya data contoh; gagal membaca berarti tombol tidak tampil, bukan halaman masuk yang rusak. */
	async check(): Promise<void> {
		try {
			this.available = (await api.demo.status()).available;
		} catch {
			this.available = false;
		}
	}

	async start(): Promise<void> {
		if (this.running && !this.error) return;
		const run = ++this.#run;
		this.running = true;
		this.error = '';
		this.shown = 0;
		this.#serverIndex = 0;
		this.#serverPercent = 0;
		try {
			this.#apply(await api.demo.start());
		} catch (failure) {
			if (run === this.#run) this.error = userMessage(failure, demoText.failedOnServer);
			return;
		}
		await this.#watch(run);
	}

	/** Kembali ke form masuk; pemantauan yang masih berjalan berhenti di putaran berikutnya. */
	cancel(): void {
		this.#run += 1;
		this.running = false;
		this.error = '';
	}

	#apply(status: DemoStatus): void {
		if (status.stage === 'failed') {
			// Kode dari status diterjemahkan lewat pintu error yang sama dengan error permintaan.
			this.error = userMessage(new ApiError(0, '', { code: status.error_code }), demoText.failedOnServer);
			return;
		}
		this.#serverIndex = Math.max(this.#serverIndex, stepIndex(status.stage));
		this.#serverPercent = status.percent;
	}

	async #watch(run: number): Promise<void> {
		const started = performance.now();
		let shownAt = started;
		let failures = 0;
		while (run === this.#run && !this.error) {
			const now = performance.now();
			if (now - started > MAX_WAIT_MILLIS) {
				this.error = demoText.tooLong;
				return;
			}
			if (this.shown < this.#serverIndex && now - shownAt >= STEP_MIN_MILLIS) {
				this.shown += 1;
				shownAt = now;
			}
			if (this.shown === READY_INDEX && now - shownAt >= STEP_MIN_MILLIS) {
				await this.#enter(run);
				return;
			}
			await pause(POLL_MILLIS);
			if (run !== this.#run || this.#serverIndex === READY_INDEX) continue;
			try {
				this.#apply(await api.demo.status());
				failures = 0;
			} catch (failure) {
				failures += 1;
				if (failures > MAX_POLL_FAILURES && run === this.#run) this.error = userMessage(failure, demoText.failedOnServer);
			}
		}
	}

	async #enter(run: number): Promise<void> {
		try {
			const result = await api.demo.enter();
			if (run !== this.#run) return;
			if (!mayEnterWeb(result.user)) {
				this.error = authText.login.noWebAccess;
				return;
			}
			saveSession(result.user);
			demoMode.set(true);
			await goto(PAGES.dashboard.path);
		} catch (failure) {
			if (run === this.#run) this.error = userMessage(failure, demoText.failedOnServer);
		}
	}
}
