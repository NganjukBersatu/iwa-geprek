/** Kurva gerak dari AppEffects, untuk transisi Svelte dan animasi lewat skrip (CSS memakai variabel --ease-*). */
export type Bezier = readonly [number, number, number, number];

export const standard: Bezier = [0.4, 0, 0.2, 1];
export const emphasized: Bezier = [0.2, 0, 0, 1];
export const bounce: Bezier = [0.34, 1.45, 0.5, 1];
export const exit: Bezier = [0.7, 0, 0.2, 1];
export const fastOutLinearIn: Bezier = [0.4, 0, 1, 1];

export const QUICK_MILLIS = 120;
export const STANDARD_MILLIS = 240;
export const SLOW_MILLIS = 400;
export const LOOP_MILLIS = 1400;

/** Fungsi easing dari kurva Bézier kubik (x1, y1, x2, y2), sama dengan CubicBezierEasing di Compose. */
export function cubicBezier([x1, y1, x2, y2]: Bezier): (progress: number) => number {
	const sampleX = (t: number) => 3 * x1 * t * (1 - t) ** 2 + 3 * x2 * t ** 2 * (1 - t) + t ** 3;
	const sampleY = (t: number) => 3 * y1 * t * (1 - t) ** 2 + 3 * y2 * t ** 2 * (1 - t) + t ** 3;
	return (progress) => {
		if (progress <= 0) return 0;
		if (progress >= 1) return 1;
		let low = 0;
		let high = 1;
		let t = progress;
		for (let step = 0; step < 24; step += 1) {
			const x = sampleX(t);
			if (Math.abs(x - progress) < 1e-5) break;
			if (x < progress) low = t;
			else high = t;
			t = (low + high) / 2;
		}
		return sampleY(t);
	};
}
