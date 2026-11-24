<script lang="ts">
	import ConfirmDialog from '$lib/components/dialog/ConfirmDialog.svelte';
	import { formatDate } from '$lib/date/range';
	import { formatRupiah } from '$lib/format/currency';
	import type { DepositsState } from '../deposits.svelte';
	import DepositDetailDialog from './DepositDetailDialog.svelte';
	import DepositFormDialog from './DepositFormDialog.svelte';
	import { depositText } from '$lib/text/deposits';
	import { format } from '$lib/text/format';

	let { deposits }: { deposits: DepositsState } = $props();
</script>

{#if deposits.form}
	<DepositFormDialog {deposits} />
{/if}

<DepositDetailDialog {deposits} />

<ConfirmDialog
	open={deposits.removing !== null}
	title={format(depositText.cancelDepositNamedTitle, { date: deposits.removing ? formatDate(deposits.removing.deposit_date) : '' })}
	confirmLabel="Batalkan"
	danger
	busy={deposits.busy}
	error={deposits.actionError}
	onconfirm={() => void deposits.confirmCancel()}
	oncancel={() => (deposits.removing = null)}
>
	{format(depositText.cancelDepositNote, { amount: deposits.removing ? formatRupiah(deposits.removing.amount) : '' })}
</ConfirmDialog>
