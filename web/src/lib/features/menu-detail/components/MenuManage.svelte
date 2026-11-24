<script lang="ts">
	import type { MenuItem } from '$lib/api/types';
	import DeleteButton from '$lib/components/button/DeleteButton.svelte';
	import Button from '$lib/components/button/Button.svelte';
	import ConfirmDialog from '$lib/components/dialog/ConfirmDialog.svelte';
	import { goto } from '$app/navigation';
	import { editAddress } from '../../record-detail/edit-address.svelte';
	import type { MenuDetailState } from '../menu-detail.svelte';
	import { actionText } from '$lib/text/actions';
	import { menuDetailText } from '$lib/text/menu-detail';
	import { format } from '$lib/text/format';

	let { menu, item, ondeleted }: { menu: MenuDetailState; item: MenuItem; ondeleted: () => void } = $props();

	async function remove(): Promise<void> {
		if (await menu.remove()) ondeleted();
	}
</script>

<Button
	label={item.is_available ? menuDetailText.markOutOfStock : menuDetailText.backInStock}
	icon={item.is_available ? 'ban' : 'circle-check'}
	variant="tertiary"
	class="w-32 justify-center"
	disabled={menu.busy}
	onclick={() => void menu.setAvailable(!item.is_available)}
/>
<Button label={actionText.edit} icon="pencil" variant="primary" disabled={menu.busy} onclick={() => void goto(editAddress().editPath)} />
<DeleteButton disabled={menu.busy} onclick={() => menu.askRemove()} />

<ConfirmDialog open={menu.removing} title={format(menuDetailText.removeNamedTitle, { name: item.name })} confirmLabel="Hapus" danger busy={menu.busy} error={menu.actionError} onconfirm={() => void remove()} oncancel={() => menu.closeDialogs()}>
	{menuDetailText.removeNote}
</ConfirmDialog>
