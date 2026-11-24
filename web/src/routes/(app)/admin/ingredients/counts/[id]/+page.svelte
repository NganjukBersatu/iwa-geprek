<script lang="ts">
	import { page } from '$app/state';
	import IngredientCountDetailView from '$lib/features/ingredient-count-detail/components/IngredientCountDetailView.svelte';
	import { IngredientCountDetailState } from '$lib/features/ingredient-count-detail/ingredient-count-detail.svelte';

	const count = new IngredientCountDetailState(page.params['id'] as string, page.url.searchParams.get('part'));
</script>

<IngredientCountDetailView {count} />
