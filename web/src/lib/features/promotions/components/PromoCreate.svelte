<script lang="ts">
	import { api } from '$lib/api';
	import type { Promo, PromoCreate, PromoMenu } from '$lib/api/types';
	import { PAGES, promoPath } from '$lib/nav/pages';
	import { createText } from '$lib/text/record-detail';
	import RecordCreateView from '../../record-detail/components/RecordCreateView.svelte';
	import { RecordCreateState } from '../../record-detail/record-create.svelte';
	import PromoForm from './PromoForm.svelte';

	const create = new RecordCreateState<Promo, PromoCreate, PromoMenu[]>({
		context: () => api.promotions.menus(),
		create: (body) => api.promotions.createPromo(body),
		name: (promo) => promo.name,
		after: (promo) => promoPath(promo.id),
		text: createText('promo')
	});
</script>

<RecordCreateView {create} back={PAGES.promotions}>
	{#snippet form(props)}
		<PromoForm promo={null} menus={props.context ?? []} busy={props.busy} error={props.error} fieldErrors={props.fieldErrors} onsave={(body) => props.onsave(body as PromoCreate)} onclose={props.onclose} />
	{/snippet}
</RecordCreateView>
