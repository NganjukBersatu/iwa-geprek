<script lang="ts">
	import { page } from '$app/state';
	import AttendanceRecordDetail from '$lib/features/attendance-list/components/AttendanceRecordDetail.svelte';
</script>

<AttendanceRecordDetail id={page.params['id'] as string} />
