import { browser } from '$app/environment';
import { get, writable } from 'svelte/store';
import { isSignedIn } from '$lib/auth/session';
import { selectedBranch } from '$lib/stores/branch';

const STREAM_PATH = '/api/web/management/live';
const DEBOUNCE_MILLISECONDS = 250;
// The server beats every 3 seconds; this long without one means the connection died silently.
const SILENCE_MILLISECONDS = 10_000;

// Waits between attempts double from the base up to the ceiling, each with a random half so many tabs do not return together; after the last attempt it waits for a person.
const RETRY_BASE_MILLISECONDS = 1000;
const RETRY_CEILING_MILLISECONDS = 30_000;
const MAX_ATTEMPTS = 8;

type Change = { tables: string[]; outlets: string[] };

/** False while the stream is lost and being reached for again; the app layout shows a strip for it. */
export const liveConnected = writable(true);
/** True once the automatic attempts are used up; the strip then offers a button instead of promising a retry. */
export const liveGaveUp = writable(false);
type Listener = { tables: Set<string>; run: () => void; timer?: ReturnType<typeof setTimeout> };

/**
 * The one door for live data: a page says which tables it shows and what to do when they change.
 * One shared connection; no polling anywhere. The server pushes a signal, never data, so `run` reloads
 * through the normal routes and should do it quietly (no dimming, no clearing).
 *
 *   onMount(() => live.on(['expenses', 'cash_sessions'], () => state.refresh()));
 */
class Live {
	private listeners = new Set<Listener>();
	private source: EventSource | null = null;
	private watchdog: ReturnType<typeof setTimeout> | undefined;
	private retryTimer: ReturnType<typeof setTimeout> | undefined;
	private attempts = 0;
	private dropped = false;

	on(tables: string[], run: () => void): () => void {
		const listener: Listener = { tables: new Set(tables), run };
		this.listeners.add(listener);
		this.connect();
		return () => {
			clearTimeout(listener.timer);
			this.listeners.delete(listener);
			if (this.listeners.size === 0) this.disconnect();
		};
	}

	/** Opens the connection again at once if someone still listens, and gives the automatic attempts a fresh start. */
	reconnect(): void {
		if (this.listeners.size === 0) return;
		clearTimeout(this.retryTimer);
		this.attempts = 0;
		liveGaveUp.set(false);
		this.connect();
	}

	private connect(): void {
		if (!browser || this.source || !isSignedIn()) return;
		// The sign-in travels in the cookie the browser sends by itself, so no token is put in the address.
		const source = new EventSource(STREAM_PATH);
		this.source = source;
		this.beat();
		let greeted = false;
		source.addEventListener('resync', () => {
			// The first resync of a connection is only hello unless it follows a drop; a later one means the server could not keep every signal for this screen.
			if (this.dropped || greeted) this.fire(() => true);
			greeted = true;
			this.dropped = false;
			this.attempts = 0;
			liveGaveUp.set(false);
			liveConnected.set(true);
		});
		source.addEventListener('detak', () => this.beat());
		source.addEventListener('ubah', (event) => {
			this.beat();
			const change = JSON.parse((event as MessageEvent<string>).data) as Change;
			const branch = get(selectedBranch);
			if (branch && change.outlets.length > 0 && !change.outlets.includes(branch)) return;
			const touched = new Set(change.tables);
			this.fire((listener) => [...listener.tables].some((table) => touched.has(table)));
		});
		source.onerror = () => {
			this.dropped = true;
			// A refusal (expired sign-in) closes the connection for good; a lost one is retried by us, with waits, not by the browser.
			if (source.readyState === EventSource.CLOSED) {
				liveConnected.set(true);
				this.disconnect();
				return;
			}
			this.lose();
		};
	}

	/** The connection died: close it, show the strip, and try again later. */
	private lose(): void {
		this.dropped = true;
		liveConnected.set(false);
		this.closeSource();
		if (this.listeners.size === 0) return;
		if (this.attempts >= MAX_ATTEMPTS) {
			liveGaveUp.set(true);
			return;
		}
		const ceiling = Math.min(RETRY_CEILING_MILLISECONDS, RETRY_BASE_MILLISECONDS * 2 ** this.attempts);
		this.attempts += 1;
		clearTimeout(this.retryTimer);
		this.retryTimer = setTimeout(() => this.connect(), ceiling / 2 + Math.random() * (ceiling / 2));
	}

	private closeSource(): void {
		clearTimeout(this.watchdog);
		this.source?.close();
		this.source = null;
	}

	private disconnect(): void {
		clearTimeout(this.retryTimer);
		this.attempts = 0;
		liveGaveUp.set(false);
		if (this.listeners.size === 0) liveConnected.set(true);
		this.closeSource();
	}

	private beat(): void {
		clearTimeout(this.watchdog);
		this.watchdog = setTimeout(() => this.lose(), SILENCE_MILLISECONDS);
	}

	/** Several signals in a burst (one save touches many tables) become one reload per listener. */
	private fire(wanted: (listener: Listener) => boolean): void {
		for (const listener of this.listeners) {
			if (!wanted(listener)) continue;
			clearTimeout(listener.timer);
			listener.timer = setTimeout(listener.run, DEBOUNCE_MILLISECONDS);
		}
	}
}

export const live = new Live();

if (browser) {
	// Back online or back on the tab after a closed connection: reconnect once, and the resync catches up.
	const reopen = () => {
		if (document.visibilityState === 'visible') live.reconnect();
	};
	document.addEventListener('visibilitychange', reopen);
	window.addEventListener('online', reopen);
}
