<script lang="ts">
	import { page } from '$app/state';
	import IngredientCountRequestDetailView from '$lib/features/ingredient-count-requests/components/IngredientCountRequestDetailView.svelte';
	import { IngredientCountRequestDetailState } from '$lib/features/ingredient-count-requests/ingredient-count-request-detail.svelte';

	const request = new IngredientCountRequestDetailState(page.params['id'] as string);
</script>

<IngredientCountRequestDetailView {request} />
