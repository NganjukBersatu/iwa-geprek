<script lang="ts">
	import { dynamicStyle } from '$lib/motion/actions';
	import Card from './Card.svelte';

	/** A row of cards, one figure each: the label small above, the value large below. */
	let { figures, label }: { figures: { label: string; value: string }[]; label: string } = $props();

	// Kartu terbanyak per baris di setiap lebar; kelebihannya dibagi rata ke beberapa baris sehingga tidak ada kartu yang tersisa sendirian.
	const MOST_PER_ROW = { tablet: 2, laptop: 4, wide: 6 } as const;

	type Rows = { tracks: number; spans: number[] };

	const greatestDivisor = (a: number, b: number): number => (b === 0 ? a : greatestDivisor(b, a % b));

	/** Membagi kartu ke baris seimbang (isi antarbaris selisih paling banyak satu), lalu setiap kartu melebar mengisi barisnya. */
	function rowsOf(count: number, mostPerRow: number): Rows {
		if (count === 0) {
			return { tracks: 1, spans: [] };
		}
		const rows = Math.ceil(count / mostPerRow);
		const small = Math.floor(count / rows);
		const fuller = count % rows;
		const large = fuller > 0 ? small + 1 : small;
		const tracks = (small * large) / greatestDivisor(small, large);
		const spans: number[] = [];
		for (let row = 0; row < rows; row++) {
			const inRow = row < fuller ? large : small;
			for (let card = 0; card < inRow; card++) {
				spans.push(tracks / inRow);
			}
		}
		return { tracks, spans };
	}

	const tablet = $derived(rowsOf(figures.length, MOST_PER_ROW.tablet));
	const laptop = $derived(rowsOf(figures.length, MOST_PER_ROW.laptop));
	const wide = $derived(rowsOf(figures.length, MOST_PER_ROW.wide));
	const tracks = (count: number): string => `repeat(${count}, minmax(0, 1fr))`;
</script>

<section
	class="grid gap-3 tablet:grid-cols-(--figure-tracks-tablet) tablet:gap-4 laptop:grid-cols-(--figure-tracks-laptop) monitor-kecil:grid-cols-(--figure-tracks-wide)"
	aria-label={label}
	use:dynamicStyle={{ '--figure-tracks-tablet': tracks(tablet.tracks), '--figure-tracks-laptop': tracks(laptop.tracks), '--figure-tracks-wide': tracks(wide.tracks) }}
>
	{#each figures as figure, index (figure.label)}
		<div
			class="flex min-w-0 tablet:col-span-(--figure-span-tablet) laptop:col-span-(--figure-span-laptop) monitor-kecil:col-span-(--figure-span-wide)"
			use:dynamicStyle={{ '--figure-span-tablet': tablet.spans[index], '--figure-span-laptop': laptop.spans[index], '--figure-span-wide': wide.spans[index] }}
		>
			<Card class="flex flex-1 flex-col gap-1">
				<span class="text-xs font-medium text-slate-500">{figure.label}</span>
				<span class="text-xl font-semibold text-slate-800 wrap-anywhere">{figure.value}</span>
			</Card>
		</div>
	{/each}
</section>
