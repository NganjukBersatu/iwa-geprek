<script lang="ts">
	import { page } from '$app/state';
	import RecipeDetail from '$lib/features/recipes/components/RecipeDetail.svelte';
</script>

<RecipeDetail id={page.params['id'] as string} />
