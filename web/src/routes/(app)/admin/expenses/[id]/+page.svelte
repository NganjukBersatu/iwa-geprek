<script lang="ts">
	import { page } from '$app/state';
	import ExpenseDetail from '$lib/features/expenses/components/ExpenseDetail.svelte';
</script>

<ExpenseDetail id={page.params['id'] as string} />
