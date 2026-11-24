<script lang="ts">
	import PrimaryButton from './PrimaryButton.svelte';

	/** Tombol pendamping tombol utama, misalnya batal; tone `danger` untuk tindakan yang membatalkan sesuatu. */
	let {
		text,
		onclick,
		enabled = true,
		tone = 'neutral',
		loading = false,
		class: className = ''
	}: {
		text: string;
		onclick?: () => void;
		enabled?: boolean;
		tone?: 'neutral' | 'danger';
		loading?: boolean;
		class?: string;
	} = $props();
</script>

<PrimaryButton
	{text}
	{onclick}
	{enabled}
	{loading}
	container={tone === 'danger' ? 'danger-container' : 'selected'}
	content={tone === 'danger' ? 'on-danger-container' : 'primary'}
	class={className}
/>
