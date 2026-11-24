<script lang="ts">
	import { page } from '$app/state';
	import SessionDetailView from '$lib/features/session-detail/components/SessionDetailView.svelte';
	import { SessionDetailState } from '$lib/features/session-detail/session-detail.svelte';

	const session = new SessionDetailState(page.params['id'] as string);
</script>

<SessionDetailView {session} />
