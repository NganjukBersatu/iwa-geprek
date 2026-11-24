<script lang="ts">
	import Button from '../button/Button.svelte';
	import type { Snippet } from 'svelte';
	import Modal from './Modal.svelte';
	import TextField from '../form/TextField.svelte';
	import { actionText } from '$lib/text/actions';
	import { format } from '$lib/text/format';

	let {
		open,
		title,
		confirmLabel,
		danger = false,
		busy = false,
		error = '',
		typeToConfirm,
		onconfirm,
		oncancel,
		children
	}: {
		open: boolean;
		title: string;
		confirmLabel: string;
		danger?: boolean;
		busy?: boolean;
		error?: string;
		/** Aksi berat: tombol baru berjalan setelah teks ini diketik persis, misalnya nama objek yang dihapus. */
		typeToConfirm?: string;
		onconfirm: () => void;
		oncancel: () => void;
		children: Snippet;
	} = $props();

	let typed = $state('');
	let mismatch = $state(false);
	const tidy = (text: string): string => text.split(/\s+/).filter(Boolean).join(' ');
	const matched = $derived(typeToConfirm === undefined || tidy(typed) === tidy(typeToConfirm));

	$effect(() => {
		if (!open) {
			typed = '';
			mismatch = false;
		}
	});

	$effect(() => {
		void typed;
		mismatch = false;
	});

	function confirm(): void {
		mismatch = !matched;
		if (matched) onconfirm();
	}
</script>

<Modal {open} {title} size="sm" {busy} onclose={oncancel}>
	<div class="text-control leading-5 text-brand-muted">{@render children()}</div>
	{#if typeToConfirm !== undefined}
		<div class="mt-3">
			<TextField label={format(actionText.typeToConfirm, { text: typeToConfirm })} bind:value={typed} disabled={busy} autocomplete="off" error={mismatch ? actionText.typeMismatch : undefined} />
		</div>
	{/if}
	{#if error}
		<p class="mt-3 rounded-lg border border-danger-200 bg-danger-50 px-3 py-2 text-xs text-danger-700" role="alert">{error}</p>
	{/if}
	{#snippet footer()}
		<Button label={actionText.cancel} disabled={busy} onclick={oncancel} />
		<Button label={busy ? actionText.processing : confirmLabel} variant={danger ? 'danger' : 'primary'} disabled={busy} onclick={confirm} />
	{/snippet}
</Modal>
