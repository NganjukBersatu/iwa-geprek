<script lang="ts">
	import { page } from '$app/state';
	import ShiftCodeDetail from '$lib/features/shift-codes/components/ShiftCodeDetail.svelte';
</script>

<ShiftCodeDetail id={page.params['id'] as string} />
