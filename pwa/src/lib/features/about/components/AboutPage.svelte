<script lang="ts">
	import { dynamicStyle } from '$lib/platform/dynamic-style';
	import DividedItems from '$lib/components/card/DividedItems.svelte';
	import IconBadge from '$lib/components/card/IconBadge.svelte';
	import ListCard from '$lib/components/card/ListCard.svelte';
	import ListRow from '$lib/components/card/ListRow.svelte';
	import Divider from '$lib/components/feedback/Divider.svelte';
	import AppIcon from '$lib/components/icon/AppIcon.svelte';
	import AppText from '$lib/components/text/AppText.svelte';
	import { PWA_RELEASE } from '$lib/features/release/release';
	import { t } from '$lib/text/t';
	import type { StringKey } from '$lib/text/strings';
	import type { IconName } from '$lib/theme/icons';

	/** Versi aplikasi yang tampil di halaman Info; diambil dari paket saat dibangun. */
	let { version }: { version: string } = $props();

	const sections: { icon: IconName; title: StringKey; text: StringKey }[] = [
		{ icon: 'Info', title: 'about_purpose_title', text: 'about_purpose' },
		{ icon: 'HeartHandshake', title: 'about_thanks_title', text: 'about_thanks' }
	];
</script>

{#snippet header(icon: IconName, title: string)}
	<div class="flex w-full items-center gap-3 p-3">
		<IconBadge {icon} />
		<AppText role="title">{title}</AppText>
	</div>
{/snippet}

<div class="flex size-full justify-center overflow-y-auto" use:dynamicStyle={{ padding: '0 var(--page-padding)' }}>
	<div class="flex w-full max-w-[var(--size-content-max)] flex-col gap-3 py-4">
		<div class="flex flex-col items-center gap-3 rounded-field bg-primary px-4 py-6">
			<img src="/brand-logo.png" alt="" class="size-[var(--size-avatar-large)] rounded-field object-cover" />
			<div class="flex flex-col items-center">
				<AppText role="headline" color="on-primary" align="center">{t('splash_app_name')}</AppText>
				<AppText role="body" color="on-primary-muted" align="center">{t('about_place')}</AppText>
			</div>
			<span class="flex items-center gap-1 rounded-full bg-on-primary-subtle px-3 py-1">
				<AppIcon icon="Apps" tint="on-primary" size={20} />
				<AppText role="label" color="on-primary">{t('about_version_line', version)}</AppText>
			</span>
		</div>
		<ListCard>
			{@render header('Sparkles', t('release_title', PWA_RELEASE.version))}
			<Divider />
			<DividedItems items={PWA_RELEASE.notes}>
				{#snippet row(note)}
					<ListRow title={t(note.key)}>
						{#snippet leading()}<IconBadge icon={note.icon} />{/snippet}
					</ListRow>
				{/snippet}
			</DividedItems>
		</ListCard>
		{#each sections as section (section.title)}
			<ListCard>
				{@render header(section.icon, t(section.title))}
				<Divider />
				<div class="p-4"><AppText role="body">{t(section.text)}</AppText></div>
			</ListCard>
		{/each}
		<div class="flex items-center justify-center gap-1 py-2">
			<AppIcon icon="Code" tint="content-muted" size={20} />
			<AppText role="caption" color="content-muted">{t('about_developer_line')}</AppText>
		</div>
	</div>
</div>
