<script lang="ts">
	import Chip from './Chip.svelte';

	/** Pilihan tunggal dalam satu baris di semua lebar layar; bila tidak muat, baris digeser ke samping, tidak turun. */
	let { label, options, selectedIndex, onselect }: { label: string; options: readonly string[]; selectedIndex: number | null; onselect: (index: number) => void } = $props();
</script>

<div class="flex flex-col gap-1">
	<span class="text-label text-content">{label}</span>
	<div class="flex gap-2 overflow-x-auto">
		{#each options as option, index (index)}
			<div class="shrink-0"><Chip label={option} selected={index === selectedIndex} onclick={() => onselect(index)} /></div>
		{/each}
	</div>
</div>
