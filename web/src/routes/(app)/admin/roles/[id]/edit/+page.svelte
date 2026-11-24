<script lang="ts">
	import { page } from '$app/state';
	import RoleDetail from '$lib/features/roles/components/RoleDetail.svelte';
</script>

<RoleDetail id={page.params['id'] as string} />
