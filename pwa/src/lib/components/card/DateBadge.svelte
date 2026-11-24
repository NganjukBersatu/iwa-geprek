<script lang="ts">
	/** Hari singkat di atas nomor tanggal, untuk baris daftar per hari. */
	let { weekday, day }: { weekday: string; day: string } = $props();
</script>

<div class="flex w-[var(--space-touch)] flex-col items-start">
	<span class="text-caption text-content-muted">{weekday}</span>
	<span class="text-button text-content">{day}</span>
</div>
