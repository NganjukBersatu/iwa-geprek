import { browser } from '$app/environment';
import { get } from 'svelte/store';
import { clearSession, isSignedIn } from '$lib/auth/session';
import { navProgress } from '$lib/motion/progress.svelte';
import { signInPathFor } from '$lib/nav/return-to';
import { branchChecked, selectedBranch } from '$lib/stores/branch';
import { demoMode } from '$lib/stores/demo-mode.svelte';
import { errorText } from '$lib/text/errors';
import { ServerClock } from '$lib/time/server-clock';

const BASE_URL = '/api';
const OFFLINE_STATUS = 0;
const OFFLINE_CODE = 'OFFLINE';
const UNREADABLE_CODE = 'UNREADABLE_RESPONSE';
const REQUEST_ID_HEADER = 'x-request-id';
/** Web admin menyebut dirinya supaya pemeriksa versi aplikasi tidak pernah mengira peramban admin sebagai PWA lama. */
const CLIENT_HEADERS = { 'X-App-Client': 'web' };

/** What the server (or this client) said about a failure, besides its status. */
type ApiErrorDetails = {
	/** The stable code of the rule, which decides the sentence shown. */
	code?: string | null;
	requestId?: string | null;
	/** How long the server asks to wait, from Retry-After. */
	retryAfterSeconds?: number | null;
	/** The sentence the server wrote, only when it wrote one. */
	serverMessage?: string | null;
	/** One sentence per refused field, keyed by the field's name in the request body. */
	fieldErrors?: Record<string, string>;
};

export class ApiError extends Error {
	readonly code: string | null;
	readonly requestId: string | null;
	readonly retryAfterSeconds: number | null;
	readonly serverMessage: string | null;
	readonly fieldErrors: Record<string, string>;

	constructor(
		public status: number,
		message: string,
		details: ApiErrorDetails = {}
	) {
		super(message);
		this.name = 'ApiError';
		this.code = details.code ?? null;
		this.requestId = details.requestId ?? null;
		this.retryAfterSeconds = details.retryAfterSeconds ?? null;
		this.serverMessage = details.serverMessage ?? null;
		this.fieldErrors = details.fieldErrors ?? {};
	}
}

function failure(response: Response, data: unknown, fallbackMessage: string): ApiError {
	const body = (data && typeof data === 'object' ? data : {}) as { code?: unknown; detail?: unknown; request_id?: unknown; fields?: unknown };
	const retry = Number.parseInt(response.headers.get('retry-after') ?? '', 10);
	const serverMessage = messageFromDetail(body.detail) || null;
	return new ApiError(response.status, serverMessage ?? fallbackMessage, {
		code: typeof body.code === 'string' ? body.code : null,
		requestId: response.headers.get(REQUEST_ID_HEADER) ?? (typeof body.request_id === 'string' ? body.request_id : null),
		retryAfterSeconds: Number.isFinite(retry) && retry > 0 ? retry : null,
		serverMessage,
		fieldErrors: { ...fieldErrorsFromDetail(body.detail), ...fieldsFromBody(body.fields) }
	});
}

type Query = Record<string, string | number | boolean | null | undefined>;

/** The order a sortable list asks the server for: a column key, "-" in front for descending. */
export type SortParam = { sort?: string };

export function toQuery(params: Query = {}): string {
	const query = new URLSearchParams();
	for (const [key, value] of Object.entries(params)) {
		if (value !== undefined && value !== null && value !== '') query.set(key, String(value));
	}
	return query.toString();
}

/** A request about one row goes to the branch that row belongs to, whatever branch the filter shows. */
export function inBranch(path: string, outletId: string): string {
	return `${path}${path.includes('?') ? '&' : '?'}outlet_id=${encodeURIComponent(outletId)}`;
}

/** Cabang terpilih ikut terkirim; cabang yang diingat dipastikan masih ada dulu supaya cabang terhapus tidak terkirim. */
async function withBranch(path: string, scoped: boolean): Promise<string> {
	if (!scoped || path.includes('outlet_id=')) return path;
	if (get(selectedBranch)) await branchChecked();
	const branch = get(selectedBranch);
	if (!branch) return path;
	return `${path}${path.includes('?') ? '&' : '?'}outlet_id=${encodeURIComponent(branch)}`;
}

/** The refused fields of a validation answer: the last step of each `loc` is the field's name, the first sentence per field wins. */
function fieldErrorsFromDetail(detail: unknown): Record<string, string> {
	const fields: Record<string, string> = {};
	if (!Array.isArray(detail)) return fields;
	for (const item of detail) {
		if (!item || typeof item !== 'object' || !('loc' in item) || !('msg' in item) || !Array.isArray(item.loc)) continue;
		const name = item.loc[item.loc.length - 1];
		if (typeof name === 'string' && !(name in fields)) fields[name] = String(item.msg);
	}
	return fields;
}

/** The fields a business rule refused, which the server names in `fields`: field name to sentence. */
function fieldsFromBody(fields: unknown): Record<string, string> {
	if (!fields || typeof fields !== 'object') return {};
	return Object.fromEntries(Object.entries(fields).filter(([, message]) => typeof message === 'string')) as Record<string, string>;
}

function messageFromDetail(detail: unknown): string | undefined {
	if (typeof detail === 'string') return detail;
	if (!Array.isArray(detail)) return undefined;
	return detail
		.map((item) => (item && typeof item === 'object' && 'msg' in item ? String(item.msg) : String(item)))
		.join('; ');
}

async function send(path: string, init?: RequestInit, scoped = true): Promise<Response> {
	const target = await withBranch(path, scoped);
	navProgress.requestStarted();
	try {
		const response = await fetch(`${BASE_URL}${target}`, {
			...init,
			// A file upload leaves the content type to the browser, which adds the multipart boundary.
			headers: { ...CLIENT_HEADERS, ...(init?.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }), ...init?.headers }
		});
		ServerClock.sync(response.headers.get('date'));
		demoMode.observe(response.headers);
		return response;
	} catch (error) {
		console.warn(`[api] tidak ada balasan yang bisa dibaca dari ${path}`, error);
		throw new ApiError(OFFLINE_STATUS, errorText.codes[OFFLINE_CODE] ?? errorText.unknown, { code: OFFLINE_CODE });
	} finally {
		navProgress.requestEnded();
	}
}

function rejectUnauthorized(status: number): void {
	if (status === 401 && isSignedIn()) {
		clearSession();
		if (browser) window.location.href = signInPathFor(window.location.pathname + window.location.search);
	}
}

/** scoped false: permintaan yang tidak boleh ditempeli cabang terpilih, misalnya daftar cabang itu sendiri. */
export async function request<T>(path: string, init?: RequestInit, scoped = true): Promise<T> {
	const response = await send(path, init, scoped);
	const text = response.status === 204 ? '' : await response.text();

	let data: unknown;
	if (text) {
		try {
			data = JSON.parse(text);
		} catch {
			if (response.status !== 401 && response.status !== 403) {
				throw new ApiError(response.status, errorText.codes[UNREADABLE_CODE] ?? errorText.unknown, {
					code: UNREADABLE_CODE,
					requestId: response.headers.get(REQUEST_ID_HEADER)
				});
			}
		}
	}

	if (!response.ok) {
		rejectUnauthorized(response.status);
		throw failure(response, data, `API error ${response.status}: ${path}`);
	}
	return data as T;
}

/** A file the server builds from a body, with the name it chose; null when the browser does not let the page read the name. */
export async function postForFile(path: string, body: unknown): Promise<{ blob: Blob; filename: string | null }> {
	const response = await send(path, { method: 'POST', body: JSON.stringify(body) });
	if (!response.ok) {
		rejectUnauthorized(response.status);
		const data: unknown = await response.json().catch(() => undefined);
		throw failure(response, data, `Download failed (${response.status}): ${path}`);
	}
	const named = /filename="([^"]+)"/.exec(response.headers.get('content-disposition') ?? '');
	return { blob: await response.blob(), filename: named?.[1] ?? null };
}

export function post<T>(path: string, body: unknown): Promise<T> {
	return request<T>(path, { method: 'POST', body: JSON.stringify(body) });
}

export function patch<T>(path: string, body: unknown): Promise<T> {
	return request<T>(path, { method: 'PATCH', body: JSON.stringify(body) });
}

export function put<T>(path: string, body: unknown): Promise<T> {
	return request<T>(path, { method: 'PUT', body: JSON.stringify(body) });
}

export function upload<T>(path: string, field: string, file: Blob, method: 'POST' | 'PUT' = 'POST'): Promise<T> {
	const body = new FormData();
	body.append(field, file);
	return request<T>(path, { method, body });
}

export function del(path: string): Promise<void> {
	return request<void>(path, { method: 'DELETE' });
}
