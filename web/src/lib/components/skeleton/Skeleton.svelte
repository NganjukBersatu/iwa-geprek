<script lang="ts">
	let { class: className = 'h-4 w-full' }: { class?: string } = $props();
</script>

<span class="skeleton-shimmer block rounded-md {className}" aria-hidden="true"></span>
