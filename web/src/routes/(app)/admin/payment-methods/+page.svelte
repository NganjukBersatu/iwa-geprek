<script lang="ts">
	import { paymentMethodNewPath } from '$lib/nav/pages';
	import { goto } from '$app/navigation';
	import Button from '$lib/components/button/Button.svelte';
	import ManageShell from '$lib/features/manage/ManageShell.svelte';
	import PaymentMethodsView from '$lib/features/payment-methods/components/PaymentMethodsView.svelte';
	import { PaymentMethodsState } from '$lib/features/payment-methods/payment-methods.svelte';
	import { termText } from '$lib/text/terms';
	import { pageText } from '$lib/text/pages';

	const methods = new PaymentMethodsState();
</script>

<ManageShell
	manage={methods}
	filters={methods.filters}
	title={termText.payment}
	description={pageText.paymentMethodsDescription}
	loadingText={pageText.loadingPaymentMethods}
>
	{#snippet actions()}
		<Button label={pageText.addMethod} icon="plus" variant="primary" compact onclick={() => void goto(paymentMethodNewPath())} />
	{/snippet}
	{#snippet children()}
		<PaymentMethodsView {methods} />
	{/snippet}
</ManageShell>
