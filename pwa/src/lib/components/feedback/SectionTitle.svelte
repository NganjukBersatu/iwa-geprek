<script lang="ts">
	/** Judul bagian halaman di atas sekelompok isi. */
	let { text, padded = true, class: className = '' }: { text: string; padded?: boolean; class?: string } = $props();
</script>

<p class="text-label m-0 text-content-muted {padded ? 'pt-6 pb-2' : ''} {className}">{text}</p>
