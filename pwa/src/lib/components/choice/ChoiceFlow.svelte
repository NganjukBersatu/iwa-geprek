<script lang="ts">
	import Chip from './Chip.svelte';

	/** Pilihan tunggal dari banyak opsi: chip turun ke baris berikutnya, tidak terpotong di tepi layar. */
	let { label, options, selectedIndex, onselect }: { label: string; options: readonly string[]; selectedIndex: number | null; onselect: (index: number) => void } = $props();
</script>

<div class="flex flex-col gap-1">
	<span class="text-label text-content">{label}</span>
	<div class="flex flex-wrap gap-2">
		{#each options as option, index (index)}
			<Chip label={option} selected={index === selectedIndex} onclick={() => onselect(index)} />
		{/each}
	</div>
</div>
