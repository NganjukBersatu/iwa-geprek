<script lang="ts">
	import { api } from '$lib/api';
	import type { PaymentMethod, PaymentMethodCreate } from '$lib/api/types';
	import { PAGES, paymentMethodPath } from '$lib/nav/pages';
	import { createText } from '$lib/text/record-detail';
	import RecordCreateView from '../../record-detail/components/RecordCreateView.svelte';
	import { RecordCreateState } from '../../record-detail/record-create.svelte';
	import PaymentMethodForm from './PaymentMethodForm.svelte';

	type MethodSave = { body: PaymentMethodCreate; outletId: string };

	const create = new RecordCreateState<PaymentMethod, MethodSave>({
		create: ({ body, outletId }) => api.paymentMethods.create(outletId, body),
		name: (method) => method.label,
		after: (method) => paymentMethodPath(method.id),
		text: createText('metode pembayaran')
	});
</script>

<RecordCreateView {create} back={PAGES.paymentMethods}>
	{#snippet form(props)}
		<PaymentMethodForm
			method={null}
			busy={props.busy}
			error={props.error}
			fieldErrors={props.fieldErrors}
			onsave={(body, outletId) => props.onsave({ body: body as PaymentMethodCreate, outletId })}
			onupload={() => undefined}
			onremoveimage={() => undefined}
			onclose={props.onclose}
		/>
	{/snippet}
</RecordCreateView>
