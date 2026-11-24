import { flip, type AnimationConfig } from 'svelte/animate';
import { fly, slide, type FlyParams, type SlideParams, type TransitionConfig } from 'svelte/transition';
import { motionMs } from './reduced';
import { DURATION, EASING } from './tokens';

/** A panel unfolding under the control that opened it. */
export function unfold(node: Element, params: SlideParams = {}): TransitionConfig {
	return slide(node, { duration: motionMs(DURATION.standard), easing: EASING.enter, ...params });
}

/** A tab's content arriving: a short rise. */
export function enter(node: Element, params: FlyParams = {}): TransitionConfig {
	return fly(node, { y: 8, duration: motionMs(DURATION.standard), easing: EASING.enter, ...params });
}

/** Content taking the place of its skeleton: it rises a little and sharpens from a slight blur. */
export function reveal(node: Element): TransitionConfig {
	return {
		delay: motionMs(60),
		duration: motionMs(DURATION.data),
		easing: EASING.enter,
		css: (t, u) => `opacity: ${t}; transform: translateY(${-10 * u}px); filter: blur(${3 * u}px)`
	};
}

/** Rows sliding to their new place when the order changes; used as animate:reorder on the item of a keyed each. */
export function reorder(node: Element, rects: { from: DOMRect; to: DOMRect }): AnimationConfig {
	return flip(node, rects, { duration: motionMs(DURATION.standard), easing: EASING.move });
}
