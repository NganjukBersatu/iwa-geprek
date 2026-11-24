export type PhotoItem = { url: string | null; caption: string };

/** Satu foto atau video yang baru dipilih dan belum diunggah. */
export type PickedMedia = { kind: 'photo' | 'video'; blob: Blob; mimeType: string; fileName: string };

/** Satu lampiran tersimpan di server; [removable] false untuk lampiran lama yang tidak boleh dihapus. */
export type RemoteAttachment = { id: string; isVideo: boolean; url: string; removable: boolean };
