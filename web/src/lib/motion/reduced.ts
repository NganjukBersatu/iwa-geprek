import { prefersReducedMotion } from 'svelte/motion';

/** Whether the viewer asked the system for less movement; the one place that reads it. */
export function motionReduced(): boolean {
	return prefersReducedMotion.current;
}

/** The one check for "reduce motion": a duration becomes 0 when the viewer asked the system for less movement. */
export function motionMs(duration: number): number {
	return motionReduced() ? 0 : duration;
}
