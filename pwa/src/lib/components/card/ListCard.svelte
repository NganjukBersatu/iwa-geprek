<script lang="ts">
	import type { Snippet } from 'svelte';

	/** Wadah putih berbingkai untuk deretan baris; pemisah antarbaris dipasang pemanggil. */
	let { children, class: className = '' }: { children: Snippet; class?: string } = $props();
</script>

<div class="w-full overflow-hidden rounded-field border border-divider bg-surface {className}">
	{@render children()}
</div>
