<script lang="ts">
	import { dynamicStyle } from '$lib/platform/dynamic-style';
	/** Saklar nyala-mati dengan [label] di kirinya; seluruh baris bisa diketuk. */
	let { label, checked, onchange }: { label: string; checked: boolean; onchange: (checked: boolean) => void } = $props();

	const TRACK_WIDTH = 48;
	const TRACK_HEIGHT = 28;
	const THUMB = 24;
	const INSET = (TRACK_HEIGHT - THUMB) / 2;
</script>

<button type="button" role="switch" aria-checked={checked} onclick={() => onchange(!checked)} class="flex items-center gap-2">
	<span class="text-label text-content">{label}</span>
	<span
		class="relative block shrink-0 rounded-full {checked ? 'bg-primary' : 'bg-outline'}"
		use:dynamicStyle={{ width: `${TRACK_WIDTH}px`, height: `${TRACK_HEIGHT}px`, opacity: checked ? 1 : 0.5 }}
	>
		<span
			class="absolute top-0 block rounded-full bg-on-primary"
			use:dynamicStyle={{ width: `${THUMB}px`, height: `${THUMB}px`, top: `${INSET}px`, transform: `translateX(${checked ? TRACK_WIDTH - THUMB - INSET : INSET}px)`, transition: 'transform var(--effect-standard) var(--ease-standard)' }}
		></span>
	</span>
</button>
