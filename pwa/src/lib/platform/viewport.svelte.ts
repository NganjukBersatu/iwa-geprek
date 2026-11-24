import { browser } from '$app/environment';

/** Ukuran jendela (WindowSize di app): Tiny sampai 360, Compact sampai 640, Medium sampai 860, selebihnya Expanded. */
export type WindowSize = 'tiny' | 'compact' | 'medium' | 'expanded';

function sizeOf(width: number): WindowSize {
	if (width <= 360) return 'tiny';
	if (width <= 640) return 'compact';
	if (width <= 860) return 'medium';
	return 'expanded';
}

class Viewport {
	width = $state(browser ? window.innerWidth : 390);
	height = $state(browser ? window.innerHeight : 800);
	/** Papan ketik terbuka: tinggi tampilan yang terlihat jauh lebih pendek dari jendela. */
	keyboardOpen = $state(false);

	readonly size = $derived(sizeOf(this.width));
	readonly isWide = $derived(this.size === 'medium' || this.size === 'expanded');

	constructor() {
		if (!browser) return;
		const update = () => {
			this.width = window.innerWidth;
			this.height = window.innerHeight;
			const visible = window.visualViewport?.height ?? window.innerHeight;
			this.keyboardOpen = window.innerHeight - visible > 150;
		};
		window.addEventListener('resize', update);
		window.visualViewport?.addEventListener('resize', update);
		update();
	}
}

export const viewport = new Viewport();
