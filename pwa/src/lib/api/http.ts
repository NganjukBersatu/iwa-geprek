import { browser } from '$app/environment';
import { updated } from '$app/state';
import { updateRequired } from '../platform/update-required.svelte';
import { demoMode } from '../platform/demo-mode.svelte';
import { failureOfError, failureOfStatus, unreadableAnswer, type AppFailure } from '../failure/failure';
import { ServerClock } from '../time/server-clock';

const BASE_URL = '/api';
const REQUEST_TIMEOUT_MILLIS = 30_000;
/** Kiriman berkas diberi waktu lebih lama, tetap di bawah batas 5 menit unggahan di Railway. */
const UPLOAD_TIMEOUT_MILLIS = 240_000;
/** Dikirim di setiap panggilan supaya server tahu aplikasi mana dan versi berapa yang memanggil. */
const APP_CLIENT = 'pwa';
const STATUS_UPGRADE_REQUIRED = 426;

export type ApiResult<T> = { kind: 'success'; value: T } | { kind: 'unauthorized' } | { kind: 'failure'; failure: AppFailure };

type Query = Record<string, string | number | boolean | null | undefined>;

export function toQuery(params: Query = {}): string {
	const query = new URLSearchParams();
	for (const [key, value] of Object.entries(params)) {
		if (value !== undefined && value !== null && value !== '') query.set(key, String(value));
	}
	const text = query.toString();
	return text ? `?${text}` : '';
}

const success = <T>(value: T): ApiResult<T> => ({ kind: 'success', value });

function rejected<T>(failure: AppFailure): ApiResult<T> {
	return failure.kind === 'unauthorized' ? { kind: 'unauthorized' } : { kind: 'failure', failure };
}

async function send<T>(method: string, path: string, body: unknown, parse: (text: string) => T | undefined): Promise<ApiResult<T>> {
	const where = `${method} ${path}`;
	const headers: Record<string, string> = { 'X-App-Client': APP_CLIENT, 'X-App-Version': __APP_VERSION__ };
	let payload: BodyInit | undefined;
	if (body instanceof FormData) {
		// Isian berkas: tipe isi diserahkan ke browser, yang menambah batas multipart.
		payload = body;
	} else if (body !== undefined) {
		headers['Content-Type'] = 'application/json';
		payload = JSON.stringify(body);
	}

	const controller = new AbortController();
	const timer = setTimeout(() => controller.abort(), body instanceof FormData ? UPLOAD_TIMEOUT_MILLIS : REQUEST_TIMEOUT_MILLIS);
	let response: Response;
	try {
		response = await fetch(`${BASE_URL}${path}`, { method, headers, body: payload, signal: controller.signal });
	} catch (error) {
		return { kind: 'failure', failure: failureOfError(error, where, body instanceof FormData) };
	} finally {
		clearTimeout(timer);
	}

	ServerClock.sync(response.headers.get('date'));
	demoMode.observe(response.headers);
	// Server menolak versi lama: cek rilis baru supaya penanda pembaruan muncul.
	if (browser && response.status === STATUS_UPGRADE_REQUIRED) void updated.check().catch(() => false);
	let text = '';
	try {
		text = response.status === 204 ? '' : await response.text();
	} catch (error) {
		return { kind: 'failure', failure: failureOfError(error, where) };
	}

	if (response.status >= 200 && response.status <= 299) {
		try {
			const value = parse(text);
			return value === undefined ? { kind: 'failure', failure: unreadableAnswer(response.status, where) } : success(value);
		} catch {
			return { kind: 'failure', failure: unreadableAnswer(response.status, where) };
		}
	}
	const failure = failureOfStatus(response.status, where, text || null);
	if (failure.kind === 'outdated') {
		updateRequired.require(failure.url);
		// Versi minimum dibaca supaya lembar pembaruan wajib bisa menyebutnya.
		void updateRequired.check();
	}
	return rejected(failure);
}

const parseJson = <T>(text: string): T => JSON.parse(text) as T;
const parseNothing = (): null => null;

/** Pemanggil API atas nama yang sedang masuk (cookie dikirim browser sendiri): membaca lewat [read], mengubah lewat [write]. */
export class ApiCaller {
	read<T>(path: string, params?: Query): Promise<ApiResult<T>> {
		return send<T>('GET', `${path}${toQuery(params)}`, undefined, parseJson<T>);
	}

	/** Mengubah data; jawaban tanpa isi (204) menghasilkan `null`. */
	write<T = null>(method: 'POST' | 'PUT' | 'PATCH' | 'DELETE', path: string, body?: unknown, parse?: (text: string) => T): Promise<ApiResult<T>> {
		return send<T>(method, path, body, parse ?? ((text: string) => (text ? parseJson<T>(text) : (parseNothing() as T))));
	}
}

/** Panggilan sebelum masuk, hanya untuk masuk. */
export function anonymousPost<T>(path: string, body: unknown): Promise<ApiResult<T>> {
	return send<T>('POST', path, body, parseJson<T>);
}


