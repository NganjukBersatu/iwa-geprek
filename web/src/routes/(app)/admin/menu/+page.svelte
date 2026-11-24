<script lang="ts">
	import { termText } from '$lib/text/terms';
	import { menuBulkPath, menuNewPath } from '$lib/nav/pages';
	import { goto } from '$app/navigation';
	import AddButton from '$lib/components/button/AddButton.svelte';
	import MoreButton from '$lib/components/button/MoreButton.svelte';
	import ManageShell from '$lib/features/manage/ManageShell.svelte';
	import MenuView from '$lib/features/menu/components/MenuView.svelte';
	import { MenuState } from '$lib/features/menu/menu.svelte';
	import { menuColumns } from '$lib/features/menu/columns';
	import { pageText } from '$lib/text/pages';

	const menu = new MenuState();
</script>

<ManageShell manage={menu} filters={menu.filters} title={pageText.menuTitle} description={pageText.menuDescription} loadingText={pageText.loadingMenu}>
	{#snippet actions()}
		<AddButton label={pageText.addMenu} onone={() => void goto(menuNewPath())} onmany={() => void goto(menuBulkPath())} />
		<MoreButton selection={menu.selection} exporter={{ title: termText.menu, columns: menuColumns(menu.outlets), rows: () => menu.exportRows() }} />
	{/snippet}
	{#snippet children()}
		<MenuView {menu} />
	{/snippet}
</ManageShell>
