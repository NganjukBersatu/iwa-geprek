<script lang="ts">
	import { unsavedText } from '$lib/text/form';
	import Button from '../button/Button.svelte';
	import Modal from './Modal.svelte';

	let { open, ondiscard, onstay }: { open: boolean; ondiscard: () => void; onstay: () => void } = $props();
</script>

<Modal {open} title={unsavedText.title} size="sm" onclose={onstay}>
	<p class="text-control leading-5 text-brand-muted">{unsavedText.body}</p>
	{#snippet footer()}
		<Button label={unsavedText.discard} variant="danger" onclick={ondiscard} />
		<Button label={unsavedText.stay} onclick={onstay} />
	{/snippet}
</Modal>
