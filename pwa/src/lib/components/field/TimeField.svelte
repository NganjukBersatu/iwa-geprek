<script lang="ts">
	import PickerField from './PickerField.svelte';

	/** Isian jam berformat "HH:MM" yang tampil seperti kolom teks dan membuka pemilih jam bawaan perangkat saat diketuk. */
	let { label, value, onchange, enabled = true }: { label: string; value: string; onchange: (time: string) => void; enabled?: boolean } = $props();
</script>

<div class="relative w-full">
	<PickerField {label} valueText={value} icon="Clock" {enabled} onclick={() => undefined} />
	<!-- Pemilih jam bawaan perangkat dipasang transparan tepat di atas kolom, supaya ketukan membukanya langsung. -->
	<input
		type="time"
		{value}
		disabled={!enabled}
		aria-label={label}
		onchange={(event) => event.currentTarget.value && onchange(event.currentTarget.value)}
		class="absolute right-0 bottom-0 left-0 h-[var(--space-touch)] w-full opacity-0"
	/>
</div>
