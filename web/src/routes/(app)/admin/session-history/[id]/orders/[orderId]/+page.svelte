<script lang="ts">
	import { page } from '$app/state';
	import OrderPage from '$lib/features/session-detail/components/OrderPage.svelte';
</script>

<OrderPage sessionId={page.params['id'] as string} id={page.params['orderId'] as string} />
