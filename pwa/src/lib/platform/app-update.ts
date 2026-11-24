import { browser, version } from '$app/environment';
import { beforeNavigate } from '$app/navigation';
import { updated } from '$app/state';
import { onMount } from 'svelte';
import { TAKE_OVER } from './release';
import { updateRequired } from './update-required.svelte';

const RELOAD_MARK = 'app-update:reloaded';

/**
 * Keeps the open PWA on the current release without breaking what is on screen: a new release is noticed when the app
 * comes back to the foreground or back online, and is loaded on the next navigation as a full page load.
 */
export function keepAppCurrent(): void {
	beforeNavigate(({ willUnload, to, cancel }) => {
		if (!updated.current || willUnload || !to?.url) return;
		cancel();
		location.href = to.url.href;
	});

	onMount(() => {
		const check = () => {
			if (document.visibilityState !== 'visible' || !navigator.onLine) return;
			void updated.check().catch(() => false);
			void updateRequired.check();
		};
		const reloadOnce = (event: Event) => {
			// A missing chunk means this release's files are gone from both cache and server; one reload fetches the current release.
			if (readMark() === version || !writeMark(version)) return;
			event.preventDefault();
			location.reload();
		};
		document.addEventListener('visibilitychange', check);
		window.addEventListener('online', check);
		window.addEventListener('vite:preloadError', reloadOnce);
		void handOverToOwnRelease();
		void updateRequired.check();
		return () => {
			document.removeEventListener('visibilitychange', check);
			window.removeEventListener('online', check);
			window.removeEventListener('vite:preloadError', reloadOnce);
		};
	});
}

// Private browsing can refuse storage; the page then never reloads on its own, so a missing file cannot start a reload loop.
function readMark(): string | null {
	try {
		return sessionStorage.getItem(RELOAD_MARK);
	} catch {
		return null;
	}
}

function writeMark(value: string): boolean {
	try {
		sessionStorage.setItem(RELOAD_MARK, value);
		return true;
	} catch {
		return false;
	}
}

/** A waiting worker built for this same release takes over; one from another release keeps waiting until the page reloads into it. */
async function handOverToOwnRelease(): Promise<void> {
	if (!browser || !('serviceWorker' in navigator)) return;
	const registration = await navigator.serviceWorker.getRegistration().catch(() => undefined);
	if (!registration) return;
	const offer = () => registration.waiting?.postMessage({ type: TAKE_OVER, version });
	offer();
	registration.addEventListener('updatefound', () => {
		const incoming = registration.installing;
		incoming?.addEventListener('statechange', () => {
			if (incoming.state === 'installed') offer();
		});
	});
}
