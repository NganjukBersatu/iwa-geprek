<script lang="ts">
	import { page } from '$app/state';
	import OrderNoteDetail from '$lib/features/order-notes/components/OrderNoteDetail.svelte';
</script>

<OrderNoteDetail id={page.params['id'] as string} />
