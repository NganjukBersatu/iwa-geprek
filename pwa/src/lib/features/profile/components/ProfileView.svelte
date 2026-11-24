<script lang="ts">
	import { dynamicStyle } from '$lib/platform/dynamic-style';
	import PrimaryButton from '$lib/components/button/PrimaryButton.svelte';
	import SecondaryButton from '$lib/components/button/SecondaryButton.svelte';
	import DetailRow from '$lib/components/card/DetailRow.svelte';
	import ListCard from '$lib/components/card/ListCard.svelte';
	import ProfileHeader from '$lib/components/card/ProfileHeader.svelte';
	import ChoiceGroup from '$lib/components/choice/ChoiceGroup.svelte';
	import PasswordField from '$lib/components/field/PasswordField.svelte';
	import TextField from '$lib/components/field/TextField.svelte';
	import Divider from '$lib/components/feedback/Divider.svelte';
	import FailureState from '$lib/components/feedback/FailureState.svelte';
	import InlineMessage from '$lib/components/feedback/InlineMessage.svelte';
	import LoadingState from '$lib/components/feedback/LoadingState.svelte';
	import SectionTitle from '$lib/components/feedback/SectionTitle.svelte';
	import PhotoSubmitForm from '$lib/components/media/PhotoSubmitForm.svelte';
	import BottomSheet from '$lib/components/sheet/BottomSheet.svelte';
	import ConfirmSheet from '$lib/components/sheet/ConfirmSheet.svelte';
	import { current } from '$lib/auth/current.svelte';
	import { displayName } from '$lib/auth/session';
	import { longDateLabel } from '$lib/format/labels';
	import { t } from '$lib/text/t';
	import { ProfileState } from '../profile.svelte';

	const NONE = '—';
	const GENDER_MALE = 'L';
	const GENDER_FEMALE = 'P';

	let { onLogout, onSessionExpired }: { onLogout: () => Promise<boolean>; onSessionExpired: () => void } = $props();

	const profile = new ProfileState(() => onSessionExpired());

	$effect(() => {
		void profile.load();
	});

	let changingPhoto = $state(false);
	let leaving = $state(false);
	let logoutFailed = $state(false);

	async function logOut(): Promise<void> {
		if (leaving) return;
		leaving = true;
		logoutFailed = !(await onLogout());
		leaving = false;
	}
	let deletingPhoto = $state(false);

	const user = $derived(current.session?.user);
	const detail = $derived(profile.detail);
	const genders = [GENDER_MALE, GENDER_FEMALE];
	const enabled = $derived(!profile.saving);

	async function uploadPhoto(photo: Blob | null): Promise<void> {
		if (photo && (await profile.uploadPhoto(photo))) changingPhoto = false;
	}

	async function removePhoto(): Promise<void> {
		if (await profile.deletePhoto()) deletingPhoto = false;
	}
</script>

{#if deletingPhoto}
	<ConfirmSheet
		title={t('profile_photo_delete_title')}
		message={profile.photoError ?? t('profile_photo_delete_message')}
		confirmLabel={t('profile_photo_delete_confirm')}
		onConfirm={() => void removePhoto()}
		onDismiss={() => {
			profile.clearPhotoError();
			deletingPhoto = false;
		}}
		destructive
		enabled={!profile.uploadingPhoto}
	/>
{/if}

{#if changingPhoto}
	<BottomSheet
		title={t('profile_photo_title')}
		onDismiss={() => {
			profile.clearPhotoError();
			changingPhoto = false;
		}}
	>
		<PhotoSubmitForm submitLabel={t('profile_photo_save')} onSubmit={(photo) => void uploadPhoto(photo)} submitting={profile.uploadingPhoto} error={profile.photoError} />
		{#if detail?.photoUrl}
			<div class="pt-3">
				<SecondaryButton
					text={t('profile_photo_delete')}
					onclick={() => {
						profile.clearPhotoError();
						changingPhoto = false;
						deletingPhoto = true;
					}}
					tone="danger"
					enabled={!profile.uploadingPhoto}
				/>
			</div>
		{/if}
	</BottomSheet>
{/if}

<div class="flex h-full w-full justify-center overflow-y-auto">
	<div class="w-full max-w-[var(--size-content-max)]" use:dynamicStyle={{ padding: '16px var(--page-padding)' }}>
		<ProfileHeader
			name={detail?.name ?? (user ? displayName(user) : '')}
			labels={[detail?.roleName ?? user?.roleName, detail?.outletName].filter((label): label is string => Boolean(label))}
			photoUrl={detail?.photoUrl ?? null}
			logoutLabel={t('nav_logout')}
			changePhotoLabel={t('profile_photo_change')}
			onLogout={() => void logOut()}
			onChangePhoto={detail ? () => (changingPhoto = true) : null}
		/>

		{#if logoutFailed}<InlineMessage text={t('nav_logout_failed')} class="mt-3" />{/if}

		{#if profile.loading}
			<div class="pt-6"><LoadingState /></div>
		{:else if profile.failure || !detail}
			<div class="pt-6"><FailureState failure={profile.failure ?? { kind: 'unexpected', type: 'Data kosong', where: 'detail' }} onRetry={() => void profile.load()} /></div>
		{:else}
			<SectionTitle text={t('profile_section_account')} />
			<ListCard>
				<DetailRow label={t('profile_account_username')} value={detail.username} />
				<Divider />
				<DetailRow label={t('profile_account_role')} value={detail.roleName} />
				<Divider />
				<DetailRow label={t('profile_account_outlet')} value={detail.outletName ?? NONE} />
				<Divider />
				<DetailRow label={t('profile_account_joined')} value={detail.joinedDate ? longDateLabel(detail.joinedDate) : NONE} />
				<Divider />
				<DetailRow label={t('profile_birth_date')} value={detail.birthDate ? longDateLabel(detail.birthDate) : NONE} />
			</ListCard>

			<SectionTitle text={t('profile_section_personal')} />
			<ListCard>
				<div class="flex w-full flex-col gap-3 p-3">
					<TextField bind:value={profile.form.name} label={t('profile_name')} {enabled} enterkeyhint="next" oninput={() => (profile.saveMessage = null)} />
					<TextField bind:value={profile.form.phone} label={t('profile_phone')} {enabled} type="tel" inputmode="tel" enterkeyhint="next" oninput={() => (profile.saveMessage = null)} />
					<TextField bind:value={profile.form.email} label={t('profile_email')} {enabled} type="email" inputmode="email" enterkeyhint="next" oninput={() => (profile.saveMessage = null)} />
					<TextField bind:value={profile.form.address} label={t('profile_address')} {enabled} enterkeyhint="next" oninput={() => (profile.saveMessage = null)} />
					<ChoiceGroup
						label={t('profile_gender')}
						options={[t('profile_gender_male'), t('profile_gender_female')]}
						selectedIndex={genders.indexOf(profile.form.gender ?? '') >= 0 ? genders.indexOf(profile.form.gender ?? '') : null}
						onselect={(index) => profile.edit({ gender: genders[index] ?? null })}
					/>
					<TextField bind:value={profile.form.emergencyName} label={t('profile_emergency_name')} {enabled} enterkeyhint="next" oninput={() => (profile.saveMessage = null)} />
					<TextField bind:value={profile.form.emergencyPhone} label={t('profile_emergency_phone')} {enabled} type="tel" inputmode="tel" enterkeyhint="next" oninput={() => (profile.saveMessage = null)} />
					<TextField bind:value={profile.form.emergencyRelation} label={t('profile_emergency_relation')} {enabled} enterkeyhint="done" oninput={() => (profile.saveMessage = null)} />
					{#if profile.saveMessage}
						<InlineMessage text={profile.saveMessage.text} tone={profile.saveMessage.success ? 'success' : 'error'} />
					{/if}
					<PrimaryButton text={profile.saving ? t('profile_saving') : t('profile_save')} onclick={() => void profile.save()} {enabled} loading={profile.saving} />
				</div>
			</ListCard>

			<SectionTitle text={t('profile_section_password')} />
			<ListCard>
				<div class="flex w-full flex-col gap-3 p-3">
					<PasswordField
						bind:value={profile.oldPassword}
						label={t('password_old')}
						showDescription={t('password_show')}
						hideDescription={t('password_hide')}
						enabled={!profile.changingPassword}
						oninput={() => (profile.passwordMessage = null)}
					/>
					<PasswordField
						bind:value={profile.newPassword}
						label={t('password_new')}
						showDescription={t('password_show')}
						hideDescription={t('password_hide')}
						enabled={!profile.changingPassword}
						oninput={() => (profile.passwordMessage = null)}
					/>
					<PasswordField
						bind:value={profile.confirmPassword}
						label={t('password_confirm')}
						showDescription={t('password_show')}
						hideDescription={t('password_hide')}
						enabled={!profile.changingPassword}
						oninput={() => (profile.passwordMessage = null)}
						onenter={() => void profile.changePassword()}
					/>
					{#if profile.passwordMessage}
						<InlineMessage text={profile.passwordMessage.text} tone={profile.passwordMessage.success ? 'success' : 'error'} />
					{/if}
					<PrimaryButton
						text={profile.changingPassword ? t('profile_changing') : t('profile_change_password')}
						onclick={() => void profile.changePassword()}
						enabled={!profile.changingPassword && profile.oldPassword !== ''}
						loading={profile.changingPassword}
					/>
				</div>
			</ListCard>
		{/if}
	</div>
</div>
