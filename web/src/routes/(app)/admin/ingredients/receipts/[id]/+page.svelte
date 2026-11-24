<script lang="ts">
	import { page } from '$app/state';
	import ReceiptDetail from '$lib/features/ingredient-receipts/components/ReceiptDetail.svelte';
</script>

<ReceiptDetail id={page.params['id'] as string} />
