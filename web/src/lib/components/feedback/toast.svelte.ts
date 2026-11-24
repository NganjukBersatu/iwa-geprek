const TOAST_MILLISECONDS = 5000;

/** `busy` stays with a running bar until the next message replaces it, for work that goes on while the page stays usable. */
export type ToastKind = 'ok' | 'error' | 'busy';

/** One short message; success fades by itself, an error stays until it is closed. Use the shared `toast` below, mounted once in the app layout, never a new instance. */
export class Toast {
	message = $state<{ text: string; kind: ToastKind } | null>(null);
	private timer: ReturnType<typeof setTimeout> | undefined;

	show(text: string, kind: Exclude<ToastKind, 'busy'> = 'ok'): void {
		this.message = { text, kind };
		clearTimeout(this.timer);
		if (kind === 'error') return;
		this.timer = setTimeout(() => (this.message = null), TOAST_MILLISECONDS);
	}

	dismiss(): void {
		clearTimeout(this.timer);
		this.message = null;
	}

	busy(text: string): void {
		this.message = { text, kind: 'busy' };
		clearTimeout(this.timer);
	}
}

export const toast = new Toast();
