<script lang="ts">
	import { page } from '$app/state';
	import IngredientDetail from '$lib/features/ingredients/components/IngredientDetail.svelte';
</script>

<IngredientDetail id={page.params['id'] as string} />
