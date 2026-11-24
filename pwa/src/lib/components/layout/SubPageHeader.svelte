<script lang="ts">
	import BackButton from './BackButton.svelte';

	/** Baris judul halaman turunan: tombol kembali di kiri (bila [onBack] ada) dan [title] di sampingnya. */
	let { title, onBack }: { title: string; onBack?: () => void } = $props();
</script>

<div class="flex w-full justify-center">
	<div class="flex w-full max-w-[var(--size-content-max)] items-center gap-1 px-1">
		{#if onBack}<BackButton onclick={onBack} />{/if}
		<h1 class="text-title m-0 text-content">{title}</h1>
	</div>
</div>
