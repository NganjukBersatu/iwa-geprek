<script lang="ts">
	import { api } from '$lib/api';
	import type { Extra, ExtraCategory, ExtraCreate, OptionMenu } from '$lib/api/types';
	import { PAGES, extraPath } from '$lib/nav/pages';
	import { branchList } from '$lib/stores/branch';
	import { createText } from '$lib/text/record-detail';
	import RecordCreateView from '../../record-detail/components/RecordCreateView.svelte';
	import { RecordCreateState } from '../../record-detail/record-create.svelte';
	import ExtraForm from './ExtraForm.svelte';

	type ExtraContext = { menus: OptionMenu[]; categories: ExtraCategory[]; outlets: { id: string; name: string }[] };

	const create = new RecordCreateState<Extra, ExtraCreate, ExtraContext>({
		context: async () => {
			const [menus, categories, outlets] = await Promise.all([api.options.menus(), api.options.categories(), branchList()]);
			return { menus, categories, outlets };
		},
		create: (body) => api.options.createExtra(body),
		name: (extra) => extra.name,
		after: (extra) => extraPath(extra.id),
		text: createText('ekstra')
	});
</script>

<RecordCreateView {create} back={PAGES.options}>
	{#snippet form(props)}
		<ExtraForm extra={null} menus={props.context?.menus ?? []} categories={props.context?.categories ?? []} outlets={props.context?.outlets ?? []} busy={props.busy} error={props.error} fieldErrors={props.fieldErrors} onsave={(body) => props.onsave(body as ExtraCreate)} onclose={props.onclose} />
	{/snippet}
</RecordCreateView>
