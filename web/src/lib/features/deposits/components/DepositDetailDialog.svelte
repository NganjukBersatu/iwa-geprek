<script lang="ts">
	import { dynamicStyle } from '$lib/motion/actions';
	import TextButton from '$lib/components/button/TextButton.svelte';
	import Button from '$lib/components/button/Button.svelte';
	import Badge from '$lib/components/card/Badge.svelte';
	import Modal from '$lib/components/dialog/Modal.svelte';
	import PhotoField from '$lib/components/form/PhotoField.svelte';
	import { dayLabel, formatDate } from '$lib/date/range';
	import { formatRupiah } from '$lib/format/currency';
	import type { DepositsState } from '../deposits.svelte';
	import { STATUS_LABEL, STATUS_TONE } from '../format';
	import { actionText } from '$lib/text/actions';
	import { depositText } from '$lib/text/deposits';
	import { format } from '$lib/text/format';

	let { deposits }: { deposits: DepositsState } = $props();

	const day = $derived(deposits.detailDay);
	const deposit = $derived(deposits.detailDeposit);
	const dayTitle = (iso: string) => {
		const label = dayLabel(iso);
		return `${label.weekday} ${label.day} · ${formatDate(iso)}`;
	};
	const percent = (paid: string, due: string) => Math.min(100, Math.round((Number(paid) / (Number(due) || 1)) * 100));
</script>

{#if day}
	<Modal open title={dayTitle(day.day)} description={depositText.dueDescription} size="sm" onclose={() => deposits.closeDialogs()}>
		<div class="flex flex-col gap-3 text-sm">
			<div class="flex items-center justify-between gap-2">
				<Badge tone={STATUS_TONE[day.status]}>{STATUS_LABEL[day.status]}</Badge>
				<span class="text-xs text-slate-500">{format(depositText.paidOfDue, { paid: formatRupiah(day.paid), due: formatRupiah(day.due) })}</span>
			</div>
			<div class="h-1.5 overflow-hidden rounded-full bg-slate-100" aria-hidden="true">
				<div class="h-full rounded-full {day.status === 'sebagian' ? 'bg-warning-500' : 'bg-success-500'}" use:dynamicStyle={{ width: `${percent(day.paid, day.due)}%` }}></div>
			</div>
			<ul class="flex flex-col divide-y divide-slate-100">
				{#each deposits.depositsOfDay(day.day) as item (item.id)}
					{@const share = item.days.find((entry) => entry.day === day.day)}
					<li class="flex items-center justify-between gap-2 py-2">
						<TextButton label={format(depositText.depositDateNote, { date: formatDate(item.deposit_date), note: item.photo_url ? '' : ' · tanpa nota' })} onclick={() => (deposits.detail = { kind: 'deposit', id: item.id })} />
						<span class="font-semibold text-slate-700">{formatRupiah(share?.amount ?? 0)}</span>
					</li>
				{:else}
					<li class="py-2 text-xs text-slate-500">{depositText.noDepositToday}</li>
				{/each}
			</ul>
			<div class="flex justify-between border-t border-slate-100 pt-2 font-semibold">
				<span>{depositText.stillHeld}</span>
				<span class={Number(day.left) > 0 ? 'text-danger-700' : 'text-success-700'}>{formatRupiah(day.left)}</span>
			</div>
		</div>
		{#snippet footer()}
			<Button label={actionText.close} onclick={() => deposits.closeDialogs()} />
			{#if deposits.canManage && Number(day.left) > 0}
				<Button label={depositText.depositRemaining} icon="cash" variant="primary" onclick={() => deposits.openCreate([day.day])} />
			{/if}
		{/snippet}
	</Modal>
{:else if deposit}
	<Modal open title={format(depositText.depositDate, { date: formatDate(deposit.deposit_date) })} description="{formatRupiah(deposit.amount)}{deposits.allBranches ? ` · ${deposit.outlet_name}` : ''}{deposit.user_name ? ` · dicatat ${deposit.user_name}` : ''}" size="sm" busy={deposits.busy} onclose={() => deposits.closeDialogs()}>
		<div class="flex flex-col gap-4 text-sm">
			{#if deposit.note}<p class="text-xs text-slate-600">{deposit.note}</p>{/if}
			<ul class="flex flex-col divide-y divide-slate-100">
				{#each deposit.days as share (share.day)}
					<li class="flex items-center justify-between gap-2 py-2">
						<TextButton label={dayTitle(share.day)} onclick={() => (deposits.detail = { kind: 'day', id: share.day })} />
						<span class="font-semibold text-slate-700">{formatRupiah(share.amount)}</span>
					</li>
				{/each}
			</ul>
			{#if deposits.canManage}
				<PhotoField label={depositText.receiptPhoto} current={deposit.photo_url} alt={format(depositText.depositReceiptNamed, { date: formatDate(deposit.deposit_date) })} disabled={deposits.busy} onpick={(file) => void deposits.replacePhoto(deposit, file)} />
			{:else if deposit.photo_url}
				<img src={deposit.photo_url} alt={format(depositText.depositReceiptNamed, { date: formatDate(deposit.deposit_date) })} class="max-h-56 w-fit rounded-lg border border-slate-200 bg-white object-contain p-2" />
			{:else}
				<p class="text-xs text-slate-500">{depositText.noReceiptPhoto}</p>
			{/if}
			{#if deposits.actionError}
				<p class="rounded-lg border border-danger-200 bg-danger-50 px-3 py-2 text-xs text-danger-700" role="alert">{deposits.actionError}</p>
			{/if}
		</div>
		{#snippet footer()}
			<Button label={actionText.close} disabled={deposits.busy} onclick={() => deposits.closeDialogs()} />
			{#if deposits.canManage}
				<Button label={depositText.cancelDeposit} icon="trash" variant="danger" disabled={deposits.busy} onclick={() => deposits.askCancel(deposit)} />
			{/if}
		{/snippet}
	</Modal>
{/if}
