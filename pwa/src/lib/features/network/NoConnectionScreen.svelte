<script lang="ts">
	import CryingLogo from '$lib/components/splash/CryingLogo.svelte';
	import AppText from '$lib/components/text/AppText.svelte';
	import { t } from '$lib/text/t';

</script>

<div class="absolute inset-0 z-40 flex flex-col items-center justify-center gap-4 bg-background px-6" role="alert">
	<CryingLogo badgeIcon="WifiOff" />
	<AppText role="headline" align="center">{t('network_lost_title')}</AppText>
	<AppText role="body" color="content-muted" align="center">{t('network_lost_message')}</AppText>
</div>
