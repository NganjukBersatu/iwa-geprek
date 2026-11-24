<script lang="ts">
	/** The check that closes a large action (a bulk change, an import): it pops in and is drawn from left to right. */
	let { class: className = 'text-xl' }: { class?: string } = $props();
</script>

<i class="ti ti-circle-check success-mark {className}" aria-hidden="true"></i>
