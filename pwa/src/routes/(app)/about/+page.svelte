<script lang="ts">
	import SubPage from '$lib/components/layout/SubPage.svelte';
	import AboutPage from '$lib/features/about/components/AboutPage.svelte';
	import { t } from '$lib/text/t';
</script>

<SubPage title={t('nav_info')} backHref="/more"><AboutPage version={__APP_VERSION__} /></SubPage>
