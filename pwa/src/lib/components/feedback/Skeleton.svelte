<script lang="ts">
	/** Blok penanda isi yang belum dimuat dengan kilau; bentuk dan ukuran diatur lewat kelas. */
	let { class: className = '' }: { class?: string } = $props();
</script>

<div class="skeleton rounded-field {className}"></div>
