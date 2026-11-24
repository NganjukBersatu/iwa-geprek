import type { Handle } from '@sveltejs/kit';
import { dev } from '$app/environment';
import { env } from '$env/dynamic/private';

import { REPORT_GROUP, REPORT_PATH } from '$lib/security/csp';
import { errorText } from '$lib/text/errors';

const API_PREFIX = '/api/';
const UNAVAILABLE_CODE = 'UNAVAILABLE';
const UNAVAILABLE_STATUS = 503;
const RETRY_AFTER_SECONDS = '5';
const DEV_BACKEND = 'http://localhost:8001';
const POLICY_HEADER = 'content-security-policy';
const STRIPPED_RESPONSE_HEADERS = ['content-encoding', 'content-length', 'transfer-encoding', 'connection'];

// The local backend is whichever BACKEND_URL names, not a fixed port, so photos load whatever port the backend runs on.
function localBackendOrigin(): string {
	const configured = env.BACKEND_URL || DEV_BACKEND;
	return URL.canParse(configured) ? new URL(configured).origin : DEV_BACKEND;
}

// In development file links point at the local backend over http, which the https-only media rule would block.
function allowLocalFiles(response: Response): Response {
	const policy = response.headers.get(POLICY_HEADER);
	if (policy) response.headers.set(POLICY_HEADER, policy.replace(/(img-src|media-src)/g, `$1 ${localBackendOrigin()}`));
	return response;
}

// Added to every page the web server itself answers; the API's own answers carry the backend's headers.
const PAGE_HEADERS: Record<string, string> = {
	'x-content-type-options': 'nosniff',
	'referrer-policy': 'strict-origin-when-cross-origin',
	'permissions-policy': 'camera=(), microphone=(), geolocation=(self), payment=(), usb=()',
	'cross-origin-opener-policy': 'same-origin'
};
const HSTS = 'max-age=63072000; includeSubDomains';
const HOST_PATTERN = /^[a-z0-9.-]+(:\d+)?$/i;

/** The browser sends reports only to a secure address written in full; the host comes from the forwarded header and is checked before it goes into a header. */
function reportEndpoint(request: Request, url: URL): string | null {
	const forwarded = request.headers.get('x-forwarded-proto')?.split(',')[0]?.trim();
	if (url.protocol !== 'https:' && forwarded !== 'https') return null;
	const host = request.headers.get('x-forwarded-host')?.split(',')[0]?.trim() || url.host;
	return HOST_PATTERN.test(host) ? `https://${host}${REPORT_PATH}` : null;
}

function secured(response: Response, request: Request, url: URL): Response {
	for (const [name, value] of Object.entries(PAGE_HEADERS)) {
		if (!response.headers.has(name)) response.headers.set(name, value);
	}
	// Railway ends the TLS, so the original scheme is read from the header it forwards.
	const forwarded = request.headers.get('x-forwarded-proto')?.split(',')[0]?.trim();
	const https = url.protocol === 'https:' || forwarded === 'https';
	if (https && !response.headers.has('strict-transport-security')) response.headers.set('strict-transport-security', HSTS);
	const endpoint = reportEndpoint(request, url);
	if (endpoint && !response.headers.has('reporting-endpoints')) response.headers.set('reporting-endpoints', `${REPORT_GROUP}="${endpoint}"`);
	// A page is checked again every time; hashed files keep the long cache their own response already states.
	if (!response.headers.has('cache-control') && response.headers.get('content-type')?.startsWith('text/html')) {
		response.headers.set('cache-control', 'no-cache');
	}
	return response;
}

/** The same coded answer the API gives when it cannot serve: a client reads the code and shows its own sentence. */
function unavailable(): Response {
	const detail = errorText.codes[UNAVAILABLE_CODE];
	return new Response(JSON.stringify({ code: UNAVAILABLE_CODE, detail }), {
		status: UNAVAILABLE_STATUS,
		headers: { 'content-type': 'application/json', 'cache-control': 'no-store', 'retry-after': RETRY_AFTER_SECONDS }
	});
}

export const handle: Handle = async ({ event, resolve }) => {
	if (!event.url.pathname.startsWith(API_PREFIX)) {
		const response = await resolve(event);
		return secured(dev ? allowLocalFiles(response) : response, event.request, event.url);
	}

	const backend = (env.BACKEND_URL || (dev ? DEV_BACKEND : '')).replace(/\/+$/, '');
	if (!backend) {
		console.error('BACKEND_URL belum diatur di server web.');
		return unavailable();
	}

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
		return unavailable();
	}
};
