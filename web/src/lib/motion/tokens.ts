import { cubicIn, cubicInOut, cubicOut } from 'svelte/easing';

/** Every duration the app moves with, in milliseconds; screens pick a name, never a number. */
export const DURATION = {
	/** Hover, press, small colour changes. */
	fast: 150,
	/** Panels unfolding, rows moving, modals closing. */
	standard: 250,
	/** Modals opening, content arriving after a skeleton. */
	enter: 300,
	/** Numbers counting to a new value, a check being drawn. */
	data: 400
} as const;

/** Easings for Svelte transitions; the CSS counterparts live in styles/motion.css as --ease-*. */
export const EASING = {
	enter: cubicOut,
	exit: cubicIn,
	move: cubicInOut
} as const;
