<script lang="ts">
	import { page } from '$app/state';
	import EmployeeDetailView from '$lib/features/employee-detail/components/EmployeeDetailView.svelte';
	import { EmployeeDetailState } from '$lib/features/employee-detail/employee-detail.svelte';

	const detail = new EmployeeDetailState(page.params['id'] as string);
</script>

<EmployeeDetailView {detail} />
