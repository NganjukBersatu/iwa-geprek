<script lang="ts">
	let { text, tone = 'error', class: className = '' }: { text: string; tone?: 'error' | 'success'; class?: string } = $props();
</script>

<p
	role="status"
	aria-live="polite"
	class="text-caption m-0 w-full rounded-field border px-3 py-2 {tone === 'error' ? 'border-danger bg-danger-container text-on-danger-container' : 'border-outline bg-selected text-primary'} {className}"
>
	{text}
</p>
