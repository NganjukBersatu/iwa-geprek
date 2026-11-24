<script lang="ts">
	import { page } from '$app/state';
	import AssignmentDetail from '$lib/features/schedule/components/AssignmentDetail.svelte';
</script>

<AssignmentDetail id={page.params['id'] as string} />
