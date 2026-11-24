<script lang="ts">
	import { page } from '$app/state';
	import PaymentMethodDetail from '$lib/features/payment-methods/components/PaymentMethodDetail.svelte';
</script>

<PaymentMethodDetail id={page.params['id'] as string} />
