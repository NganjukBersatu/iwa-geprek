import type { Action } from 'svelte/action';
import { motionReduced } from './reduced';

type Head = HTMLElement | string | null;

const find = (head: Head): HTMLElement | null => (typeof head === 'string' ? document.querySelector<HTMLElement>(head) : head);

/** Gives the head above a scroll area (the element itself or a selector) a shadow once the area is scrolled. */
export const scrollShadow: Action<HTMLElement, Head> = (node, initial) => {
	let head = initial;
	const paint = () => find(head)?.toggleAttribute('data-scrolled', node.scrollTop > 0);
	const clear = () => find(head)?.removeAttribute('data-scrolled');
	node.addEventListener('scroll', paint, { passive: true });
	paint();
	return {
		update(next) {
			clear();
			head = next;
			paint();
		},
		destroy() {
			node.removeEventListener('scroll', paint);
			clear();
		}
	};
};

/** Fills a timeline as it scrolls past the reading line (sets --trace-fill) and lights each [data-trace-step] already passed. */
export const traceScroll: Action<HTMLElement> = (node) => {
	let queued = false;
	const paint = () => {
		queued = false;
		const line = window.innerHeight * 0.62;
		const box = node.getBoundingClientRect();
		const fill = motionReduced() ? 1 : Math.max(0, Math.min(1, (line - box.top) / Math.max(1, box.height)));
		node.style.setProperty('--trace-fill', fill.toFixed(3));
		for (const step of node.querySelectorAll<HTMLElement>('[data-trace-step]')) {
			step.toggleAttribute('data-lit', motionReduced() || step.getBoundingClientRect().top + 22 < line);
		}
	};
	const queue = () => {
		if (queued) return;
		queued = true;
		requestAnimationFrame(paint);
	};
	// Capture catches the scroll of whichever area scrolls the page.
	window.addEventListener('scroll', queue, { passive: true, capture: true });
	window.addEventListener('resize', queue);
	paint();
	return {
		destroy() {
			window.removeEventListener('scroll', queue, { capture: true });
			window.removeEventListener('resize', queue);
		}
	};
};

type StyleValue = string | number | null | undefined;

/** Sets inline values through the style object, which a strict style-src-attr allows; a style attribute or Svelte's style: directive does not. Empty values remove the property. */
export const dynamicStyle: Action<HTMLElement, Record<string, StyleValue>> = (node, initial) => {
	let applied = new Set<string>();
	const paint = (values: Record<string, StyleValue>) => {
		const next = new Set<string>();
		for (const [name, value] of Object.entries(values)) {
			if (value === undefined || value === null || value === '') continue;
			node.style.setProperty(name, String(value));
			next.add(name);
		}
		for (const name of applied) {
			if (!next.has(name)) node.style.removeProperty(name);
		}
		applied = next;
	};
	paint(initial);
	return { update: paint };
};

/** Menggulirkan menu yang sedang aktif ke tengah daftar saat daftar dibuka, supaya menu berikutnya mudah dicari. */
export const revealActive: Action<HTMLElement> = (node) => {
	const frame = requestAnimationFrame(() => {
		node.querySelector<HTMLElement>('[aria-current="page"]')?.scrollIntoView({ block: 'center' });
	});
	return {
		destroy() {
			cancelAnimationFrame(frame);
		}
	};
};
