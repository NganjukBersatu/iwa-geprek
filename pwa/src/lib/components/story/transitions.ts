import type { TransitionConfig } from 'svelte/transition';
import { cubicBezier, emphasized, SLOW_MILLIS } from '$lib/theme/ease';

/** Peralihan antar halaman cerita; pemutar memilihnya bergiliran supaya tiap halaman terasa berbeda. */
export const STORY_TRANSITION_KINDS = ['push', 'fade-through', 'rise', 'zoom'] as const;
export type StoryTransitionKind = (typeof STORY_TRANSITION_KINDS)[number];

const PARALLAX_DIVISOR = 3;
const RISE_DIVISOR = 4;
const THROUGH_SCALE = 0.92;
const ZOOM_FROM = 1.12;
const ZOOM_TO = 0.88;

const ease = cubicBezier(emphasized);

export type StoryTransitionParams = { kind: StoryTransitionKind; forward: boolean };

/** Peralihan masuk halaman baru. */
export function storyIn(_node: Element, { kind, forward }: StoryTransitionParams): TransitionConfig {
	const sign = forward ? 1 : -1;
	return {
		duration: SLOW_MILLIS,
		easing: ease,
		css: (t, u) => {
			switch (kind) {
				case 'push':
					return `opacity:${t};transform:translateX(${u * 100 * sign}%)`;
				case 'fade-through':
					return `opacity:${t};transform:scale(${THROUGH_SCALE + (1 - THROUGH_SCALE) * t})`;
				case 'rise':
					return `opacity:${t};transform:translateY(${(u * 100 * sign) / RISE_DIVISOR}%)`;
				default: {
					const from = forward ? ZOOM_FROM : ZOOM_TO;
					return `opacity:${t};transform:scale(${from + (1 - from) * t})`;
				}
			}
		}
	};
}

/** Peralihan keluar halaman lama. */
export function storyOut(_node: Element, { kind, forward }: StoryTransitionParams): TransitionConfig {
	const sign = forward ? 1 : -1;
	return {
		duration: SLOW_MILLIS,
		easing: ease,
		css: (t, u) => {
			switch (kind) {
				case 'push':
					return `opacity:${t};transform:translateX(${(-u * 100 * sign) / PARALLAX_DIVISOR}%)`;
				case 'fade-through':
					return `opacity:${t};transform:scale(${THROUGH_SCALE + (1 - THROUGH_SCALE) * t})`;
				case 'rise':
					return `opacity:${t};transform:translateY(${(-u * 100 * sign) / RISE_DIVISOR}%)`;
				default: {
					const to = forward ? ZOOM_TO : ZOOM_FROM;
					return `opacity:${t};transform:scale(${to + (1 - to) * t})`;
				}
			}
		}
	};
}

export type StoryPage = { title: string; body: string };
