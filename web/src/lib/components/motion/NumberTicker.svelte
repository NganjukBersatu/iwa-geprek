<script lang="ts">
	import { Tween } from 'svelte/motion';
	import { motionMs } from '$lib/motion/reduced';
	import { DURATION, EASING } from '$lib/motion/tokens';

	/** A formatted figure ("Rp 1.250.000", "12,5%", "8 orang") that counts to its new value when it changes; the final text is always the one given. */
	let { text }: { text: string } = $props();

	// One Indonesian-formatted number: dots group thousands, a comma starts the decimals.
	const NUMBER = /-?\d{1,3}(?:\.\d{3})+(?:,\d+)?|-?\d+(?:,\d+)?/;

	type Parsed = { before: string; after: string; value: number; decimals: number };

	function parse(source: string): Parsed | null {
		const match = NUMBER.exec(source);
		if (!match || NUMBER.test(source.slice(match.index + match[0].length))) return null;
		const decimals = match[0].split(',')[1]?.length ?? 0;
		const value = Number(match[0].replaceAll('.', '').replace(',', '.'));
		if (!Number.isFinite(value) || format(value, decimals) !== match[0]) return null;
		return { before: source.slice(0, match.index), after: source.slice(match.index + match[0].length), value, decimals };
	}

	function format(value: number, decimals: number): string {
		return value.toLocaleString('id-ID', { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
	}

	const parsed = $derived(parse(text));
	const tween = new Tween(0, { duration: () => motionMs(DURATION.data), easing: EASING.enter });
	let started = false;

	$effect(() => {
		const target = parsed?.value ?? 0;
		// The first value is shown as it is; only later changes count.
		void tween.set(target, started ? undefined : { duration: 0 });
		started = true;
	});

	const shown = $derived(!parsed || tween.current === parsed.value ? text : `${parsed.before}${format(tween.current, parsed.decimals)}${parsed.after}`);
</script>

<span class="tabular-nums">{shown}</span>
