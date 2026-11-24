<script lang="ts">
	import { api } from '$lib/api';
	import type { MenuCategory, MenuCreate, MenuItem } from '$lib/api/types';
	import type { BranchOption } from '$lib/components/form/branch-prices.svelte';
	import { PAGES, menuPath } from '$lib/nav/pages';
	import { branchList } from '$lib/stores/branch';
	import { createText } from '$lib/text/record-detail';
	import RecordCreateView from '../../record-detail/components/RecordCreateView.svelte';
	import { RecordCreateState } from '../../record-detail/record-create.svelte';
	import { saveMenu } from '../save';
	import MenuForm from './MenuForm.svelte';

	type MenuContext = { categories: MenuCategory[]; outlets: BranchOption[] };
	type MenuSave = { body: MenuCreate; photo: File | null };

	const create = new RecordCreateState<MenuItem, MenuSave, MenuContext>({
		context: async () => {
			const [categories, outlets] = await Promise.all([api.menu.categories(), branchList()]);
			return { categories, outlets: outlets.map((outlet) => ({ id: outlet.id, name: outlet.name })) };
		},
		create: ({ body, photo }) => saveMenu(null, body, photo),
		name: (item) => item.name,
		after: (item) => menuPath(item.id),
		text: createText('menu')
	});
</script>

<RecordCreateView {create} back={PAGES.menu}>
	{#snippet form(props)}
		<MenuForm item={null} categories={props.context?.categories ?? []} outlets={props.context?.outlets ?? []} busy={props.busy} error={props.error} fieldErrors={props.fieldErrors} onsave={(body, photo) => props.onsave({ body: body as MenuCreate, photo })} onclose={props.onclose} />
	{/snippet}
</RecordCreateView>
