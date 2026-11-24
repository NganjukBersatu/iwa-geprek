import { cubicBezier, type Bezier } from './ease';

/** Menjalankan satu animasi nilai dari [from] ke [to] selama [durationMillis]; hasilnya selesai saat nilai mencapai tujuan. */
export function animateValue(options: {
	from: number;
	to: number;
	durationMillis: number;
	easing: Bezier | ((progress: number) => number);
	delayMillis?: number;
	onUpdate: (value: number) => void;
}): { done: Promise<void>; cancel: () => void } {
	const ease = typeof options.easing === 'function' ? options.easing : cubicBezier(options.easing);
	let frame = 0;
	let cancelled = false;
	const done = new Promise<void>((resolve) => {
		const start = performance.now() + (options.delayMillis ?? 0);
		const step = (now: number) => {
			if (cancelled) return resolve();
			if (now < start) {
				frame = requestAnimationFrame(step);
				return;
			}
			const progress = Math.min(1, (now - start) / options.durationMillis);
			options.onUpdate(options.from + (options.to - options.from) * ease(progress));
			if (progress < 1) frame = requestAnimationFrame(step);
			else resolve();
		};
		options.onUpdate(options.from);
		frame = requestAnimationFrame(step);
	});
	return {
		done,
		cancel: () => {
			cancelled = true;
			cancelAnimationFrame(frame);
		}
	};
}

export const sleep = (millis: number): Promise<void> => new Promise((resolve) => setTimeout(resolve, millis));
