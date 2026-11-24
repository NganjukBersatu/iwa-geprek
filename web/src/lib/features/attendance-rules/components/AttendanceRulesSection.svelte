<script lang="ts">
	import ManageSection from '$lib/features/manage/ManageSection.svelte';
	import { attendanceRulesText } from '$lib/text/attendance-rules';
	import { AttendanceRulesState } from '../attendance-rules.svelte';
	import AttendanceRulesView from './AttendanceRulesView.svelte';

	/** Aturan absensi satu cabang di halaman detail cabang; cabangnya dibaca dari pilihan cabang yang sudah ditetapkan halaman itu. */
	const rules = new AttendanceRulesState();
</script>

<ManageSection manage={rules} loadingText={attendanceRulesText.loading}>
	<AttendanceRulesView {rules} />
</ManageSection>
