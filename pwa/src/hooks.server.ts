import type { Handle, ServerInit } from '@sveltejs/kit';
import { building, dev } from '$app/environment';
import { env } from '$env/dynamic/private';
import { bodyLimitProblem } from '$lib/api/body-limit';
import { BLOCKED_LOGO, blockedPageHtml } from '$lib/features/blocked/blocked';
import { isBlockedDevice } from '$lib/platform/device';

const API_PREFIX = '/api/';
const HEALTH_PATH = '/health';
const DEV_BACKEND = 'http://localhost:8001';
const POLICY_HEADER = 'content-security-policy';
const STRIPPED_RESPONSE_HEADERS = ['content-encoding', 'content-length', 'transfer-encoding', 'connection'];

// In development file links point at the local backend over http, which the https-only media rule would block.
function allowLocalFiles(response: Response): Response {
	const policy = response.headers.get(POLICY_HEADER);
	if (policy) response.headers.set(POLICY_HEADER, policy.replace(/(img-src|media-src)/g, `$1 ${DEV_BACKEND}`));
	return response;
}

// Server tetap berjalan bila batasnya kurang, karena login dan absen tidak boleh berhenti; masalahnya dicatat setiap start.
export const init: ServerInit = () => {
	if (dev || building) return;
	const problem = bodyLimitProblem(env.BODY_SIZE_LIMIT);
	if (problem) console.error(problem);
};

// Added to every page this server answers; the API's own answers carry the backend's headers.
const PAGE_HEADERS: Record<string, string> = {
	'x-content-type-options': 'nosniff',
	'referrer-policy': 'strict-origin-when-cross-origin',
	'permissions-policy': 'camera=(self), geolocation=(self), microphone=(), payment=(), usb=()',
	'cross-origin-opener-policy': 'same-origin'
};
const HSTS = 'max-age=63072000; includeSubDomains';

function secured(response: Response, request: Request, url: URL): Response {
	for (const [name, value] of Object.entries(PAGE_HEADERS)) {
		if (!response.headers.has(name)) response.headers.set(name, value);
	}
	// Railway ends the TLS, so the original scheme is read from the header it forwards.
	const forwarded = request.headers.get('x-forwarded-proto')?.split(',')[0]?.trim();
	if ((url.protocol === 'https:' || forwarded === 'https') && !response.headers.has('strict-transport-security')) response.headers.set('strict-transport-security', HSTS);
	// A page is checked again every time; hashed files keep the long cache their own response already states.
	if (!response.headers.has('cache-control') && response.headers.get('content-type')?.startsWith('text/html')) response.headers.set('cache-control', 'no-cache');
	return response;
}

export const handle: Handle = async ({ event, resolve }) => {
	// The platform's health check is not an iPhone, so it is answered before the device is judged.
	if (event.url.pathname === HEALTH_PATH) return new Response('ok', { status: 200, headers: { 'cache-control': 'no-store' } });
	const device = { userAgent: event.request.headers.get('user-agent') ?? '', platform: event.request.headers.get('sec-ch-ua-platform') ?? '', touchPoints: -1 };
	// Logo tetap dilayani agar halaman penolakan tidak tampil tanpa gambar.
	if (isBlockedDevice(device) && event.url.pathname !== BLOCKED_LOGO) {
		if (event.url.pathname.startsWith(API_PREFIX)) return new Response(null, { status: 403 });
		return secured(new Response(blockedPageHtml(), { status: 403, headers: { 'content-type': 'text/html; charset=utf-8' } }), event.request, event.url);
	}
	if (!event.url.pathname.startsWith(API_PREFIX)) {
		const page = dev ? allowLocalFiles(await resolve(event)) : await resolve(event);
		return secured(page, event.request, event.url);
	}

	const backend = (env.BACKEND_URL || (dev ? DEV_BACKEND : '')).replace(/\/+$/, '');
	if (!backend) return new Response('BACKEND_URL belum diatur di server web.', { status: 502 });

	const target = `${backend}/${event.url.pathname.slice(API_PREFIX.length)}${event.url.search}`;
	const headers = new Headers(event.request.headers);
	headers.delete('host');

	// The browser closing a request (a live stream left behind) also closes the call to the backend.
	const init: RequestInit & { duplex?: 'half' } = { method: event.request.method, headers, redirect: 'manual', signal: event.request.signal };
	if (event.request.method !== 'GET' && event.request.method !== 'HEAD') {
		init.body = event.request.body;
		init.duplex = 'half';
	}

	try {
		const upstream = await fetch(target, init);
		const responseHeaders = new Headers(upstream.headers);
		for (const name of STRIPPED_RESPONSE_HEADERS) responseHeaders.delete(name);
		return new Response(upstream.body, { status: upstream.status, statusText: upstream.statusText, headers: responseHeaders });
	} catch (error) {
		if (event.request.signal.aborted) return new Response(null, { status: 499 });
		console.error(`Penerus API gagal ke ${backend}:`, error, (error as { cause?: unknown }).cause);
		return new Response('Backend tidak bisa dihubungi dari server web.', { status: 502 });
	}
};
