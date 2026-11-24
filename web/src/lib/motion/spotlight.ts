import { motionReduced } from './reduced';

// Sections usually render after their data arrives, so the target is awaited this long.
const WAIT_MILLISECONDS = 5000;
const CLASS = 'spotlight';

/** Membingkai satu elemen sesaat dengan efek yang sama, dan membawanya ke posisi `block` di layar; null berarti tidak digulir. */
export function frame(target: HTMLElement, block: ScrollLogicalPosition | null = 'start'): void {
	target.classList.remove(CLASS);
	// Reading the layout restarts the frame when the same section is marked twice in a row.
	void target.offsetWidth;
	target.classList.add(CLASS);
	if (block) target.scrollIntoView({ behavior: motionReduced() ? 'auto' : 'smooth', block });
	const done = (event: AnimationEvent) => {
		if (event.target !== target) return;
		target.classList.remove(CLASS);
		target.removeEventListener('animationend', done);
	};
	target.addEventListener('animationend', done);
}

/** Brings the section with this id ("#id" or "id") into view and frames it for a moment, waiting for it to render; returns a stop for that wait. */
export function spotlight(hash: string): () => void {
	const id = decodeURIComponent(hash.replace(/^#/, ''));
	if (!id) return () => {};

	const mark = (target: HTMLElement) => frame(target);

	const now = document.getElementById(id);
	if (now) {
		mark(now);
		return () => {};
	}
	const watcher = new MutationObserver(() => {
		const target = document.getElementById(id);
		if (!target) return;
		stop();
		mark(target);
	});
	const timer = setTimeout(() => stop(), WAIT_MILLISECONDS);
	const stop = () => {
		watcher.disconnect();
		clearTimeout(timer);
	};
	watcher.observe(document.body, { childList: true, subtree: true });
	return stop;
}
