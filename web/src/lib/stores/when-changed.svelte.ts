import { untrack } from 'svelte';

/**
 * The one way a screen reloads when what it asks for changes; call it while a component starts.
 * `read` is tracked, and `run` fires only when the content differs from the last run, so a value rebuilt with the same content never loads twice.
 */
export function whenChanged<T>(read: () => T, run: (value: T) => void): void {
	let last: string | undefined;
	$effect(() => {
		const value = read();
		const key = JSON.stringify(value) ?? '';
		untrack(() => {
			if (key === last) return;
			last = key;
			run(value);
		});
	});
}
