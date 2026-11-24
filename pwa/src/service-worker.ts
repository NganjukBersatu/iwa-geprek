/// <reference types="@sveltejs/kit" />
/// <reference no-default-lib="true"/>
/// <reference lib="esnext" />
/// <reference lib="webworker" />
import { build, files, version } from '$service-worker';
import { TAKE_OVER } from '$lib/platform/release';

/**
 * Keeps the app shell so the PWA still opens without signal and shows its own offline screen instead of Safari's error page;
 * data from /api is never stored and always comes from the server.
 */
const worker = self as unknown as ServiceWorkerGlobalScope;
const CACHE = `shell-${version}`;
const SHELL = '/';
// Safari uses woff2, so the woff/ttf copies of the icon webfont are not stored.
const ASSETS = [...build.filter((path) => !/\.(woff|ttf)$/.test(path)), ...files, SHELL];

// A new worker waits instead of taking over, so a page still running the previous release keeps the files it was built with.
worker.addEventListener('install', (event) => {
	event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(ASSETS)));
});

// Only a page already running this release may hand control over, so the previous release's files are never removed under an open page.
worker.addEventListener('message', (event) => {
	const data: unknown = event.data;
	if (typeof data === 'object' && data !== null && 'type' in data && 'version' in data && data.type === TAKE_OVER && data.version === version) {
		event.waitUntil(worker.skipWaiting());
	}
});

worker.addEventListener('activate', (event) => {
	event.waitUntil(
		caches
			.keys()
			.then((keys) => Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key))))
			.then(() => worker.clients.claim())
	);
});

worker.addEventListener('fetch', (event) => {
	const request = event.request;
	if (request.method !== 'GET') return;
	const url = new URL(request.url);
	if (url.origin !== worker.location.origin || url.pathname.startsWith('/api/')) return;

	// Pages come from the network first and fall back to the stored shell when offline.
	if (request.mode === 'navigate') {
		event.respondWith(fetch(request).catch(async () => (await caches.match(SHELL)) ?? Response.error()));
		return;
	}

	// Build files never change within a release, so the stored copy comes first.
	if (ASSETS.includes(url.pathname)) {
		event.respondWith(caches.match(url.pathname).then((cached) => cached ?? fetch(request)));
	}
});
