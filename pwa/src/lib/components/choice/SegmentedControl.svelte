<script lang="ts">
	import { dynamicStyle } from '$lib/platform/dynamic-style';
	/** Pilihan satu dari beberapa opsi sejajar; penanda meluncur ke opsi terpilih. */
	let { options, selectedIndex, onselect }: { options: readonly string[]; selectedIndex: number; onselect: (index: number) => void } = $props();
</script>

<div class="relative w-full rounded-full bg-surface p-1">
	<span
		class="absolute top-1 left-1 block h-[var(--size-control)] rounded-full bg-primary"
		use:dynamicStyle={{ width: `calc((100% - 8px) / ${options.length})`, transform: `translateX(${selectedIndex * 100}%)`, transition: 'transform var(--effect-standard) var(--ease-bounce)' }}
	></span>
	<div class="relative flex">
		{#each options as option, index (index)}
			<button
				type="button"
				role="tab"
				aria-selected={index === selectedIndex}
				onclick={() => onselect(index)}
				class="text-label flex h-[var(--size-control)] flex-1 items-center justify-center rounded-full {index === selectedIndex ? 'text-on-primary' : 'text-content'}"
			>
				{option}
			</button>
		{/each}
	</div>
</div>
