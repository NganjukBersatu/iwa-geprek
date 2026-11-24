import { t } from '../text/t';

/** Satu-satunya daftar sebab gagal; teksnya hanya di [failureText] dan [where] berisi metode serta alamat yang gagal. */
export type AppFailure =
	| { kind: 'unreachable'; where: string }
	| { kind: 'timeout'; where: string; upload: boolean }
	| { kind: 'secure'; where: string }
	| { kind: 'unexpected'; type: string; where: string }
	| { kind: 'server'; code: number; where: string }
	| { kind: 'notFound'; code: number; where: string }
	| { kind: 'forbidden' }
	| { kind: 'tooLarge' }
	| { kind: 'tooMany' }
	| { kind: 'invalid' }
	| { kind: 'outdated'; message: string | null; url: string | null }
	| { kind: 'rejected'; code: number; message: string | null; reason: string | null }
	| { kind: 'unauthorized' };

/** Kode jawaban server untuk kunci pengiriman yang dipakai ulang dengan isi berbeda. */
export const REASON_KEY_REUSED = 'IDEMPOTENCY_KEY_REUSED';

const STATUS_UNAUTHORIZED = 401;
const STATUS_FORBIDDEN = 403;
const STATUS_NOT_FOUND = 404;
const STATUS_METHOD_NOT_ALLOWED = 405;
const STATUS_PAYLOAD_TOO_LARGE = 413;
const STATUS_TOO_MANY_REQUESTS = 429;
const STATUS_UPGRADE_REQUIRED = 426;

/** Menggolongkan kegagalan sebelum ada jawaban; hanya yang benar-benar soal sambungan yang dianggap tak terjangkau. */
export function failureOfError(error: unknown, where: string, upload = false): AppFailure {
	const name = error instanceof Error ? error.name : '';
	if (name === 'AbortError' || name === 'TimeoutError') return { kind: 'timeout', where, upload };
	if (error instanceof TypeError) return { kind: 'unreachable', where };
	return { kind: 'unexpected', type: name || 'Exception', where };
}

/** Kode galat validasi dari backend; hanya jawaban bertanda ini yang kalimatnya sudah berbahasa Indonesia. */
const VALIDATION_FAILED = 'VALIDATION_FAILED';

/** Isi jawaban FastAPI: kalimat dari aturan bisnis, daftar galat validasi, atau tidak ada. */
type Detail = { kind: 'text'; text: string } | { kind: 'list' } | { kind: 'none' };

function sentenceOf(item: unknown): string | null {
	const msg = (item as { msg?: unknown } | null)?.msg;
	return typeof msg === 'string' && msg.trim() !== '' ? msg : null;
}

function detailOf(body: string | null): Detail {
	if (!body) return { kind: 'none' };
	try {
		const answer = JSON.parse(body) as { code?: unknown; detail?: unknown };
		const detail = answer.detail;
		if (typeof detail === 'string' && detail.trim() !== '') return { kind: 'text', text: detail };
		if (Array.isArray(detail)) {
			// Daftar tanpa kode berasal dari backend lama (berbahasa Inggris) dan tidak ditampilkan.
			const first = answer.code === VALIDATION_FAILED ? sentenceOf(detail[0]) : null;
			return first ? { kind: 'text', text: first } : { kind: 'list' };
		}
	} catch {
		return { kind: 'none' };
	}
	return { kind: 'none' };
}

/** Kode mesin dari badan jawaban, bila ada; dipakai untuk memilih kalimat pengguna, tidak pernah ditampilkan. */
function reasonOf(body: string | null): string | null {
	try {
		const code = (JSON.parse(body ?? '') as { code?: unknown }).code;
		return typeof code === 'string' && code !== '' ? code : null;
	} catch {
		return null;
	}
}

/** Kalimat penolakan versi lama dan alamat unduhnya; alamat hanya dipakai bila diawali https. */
function outdatedOf(body: string | null): AppFailure {
	let message: string | null = null;
	let url: string | null = null;
	try {
		const answer = JSON.parse(body ?? '') as { detail?: unknown; download_url?: unknown };
		if (typeof answer.detail === 'string') message = answer.detail;
		if (typeof answer.download_url === 'string' && answer.download_url.startsWith('https://')) url = answer.download_url;
	} catch {
		// Jawaban tidak terbaca: kalimat bawaan aplikasi dipakai.
	}
	return { kind: 'outdated', message, url };
}

/** Menggolongkan jawaban server yang tidak sukses; daftar galat validasi bawaan tidak pernah ditampilkan karena bukan untuk pengguna. */
export function failureOfStatus(status: number, where: string, body: string | null): AppFailure {
	if (status === STATUS_UNAUTHORIZED) return { kind: 'unauthorized' };
	if (status === STATUS_NOT_FOUND || status === STATUS_METHOD_NOT_ALLOWED) return { kind: 'notFound', code: status, where };
	if (status === STATUS_PAYLOAD_TOO_LARGE) return { kind: 'tooLarge' };
	if (status === STATUS_TOO_MANY_REQUESTS) return { kind: 'tooMany' };
	if (status === STATUS_UPGRADE_REQUIRED) return outdatedOf(body);
	if (status >= 400 && status <= 499) {
		const detail = detailOf(body);
		if (detail.kind === 'text') return { kind: 'rejected', code: status, message: detail.text, reason: reasonOf(body) };
		if (detail.kind === 'list') return { kind: 'invalid' };
		return status === STATUS_FORBIDDEN ? { kind: 'forbidden' } : { kind: 'rejected', code: status, message: null, reason: reasonOf(body) };
	}
	return { kind: 'server', code: status, where };
}

/** Jawaban 2xx yang isinya tidak bisa dibaca dianggap gangguan di server, bukan jaringan. */
export const unreadableAnswer = (status: number, where: string): AppFailure => ({ kind: 'server', code: status, where });

export function failureText(failure: AppFailure): string {
	switch (failure.kind) {
		case 'unreachable':
			return t('web_failure_unreachable');
		case 'timeout':
			return failure.upload ? t('web_failure_upload_timeout') : t('web_failure_timeout');
		case 'secure':
			return t('web_failure_secure');
		case 'unexpected':
			return t('web_failure_unexpected');
		case 'server':
			return t('web_failure_server');
		case 'notFound':
			return t('web_failure_not_found');
		case 'forbidden':
			return t('web_failure_forbidden');
		case 'tooLarge':
			return t('web_failure_too_large');
		case 'tooMany':
			return t('web_failure_too_many');
		case 'invalid':
			return t('web_failure_invalid');
		case 'outdated':
			return failure.message ?? t('web_failure_outdated');
		case 'rejected':
			if (failure.reason === REASON_KEY_REUSED) return t('attendance_key_reused');
			return failure.message ?? t('web_failure_rejected');
		case 'unauthorized':
			return t('failure_unauthorized');
	}
}

/** True bila server tidak bisa dicapai. */
export const isOffline = (failure: AppFailure): boolean => failure.kind === 'unreachable' || failure.kind === 'timeout' || failure.kind === 'secure';
