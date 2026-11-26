package id.kongstudio.cafe.feature.devicesetup

import android.content.Context
import android.os.Build
import android.provider.Settings
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import java.security.KeyStore
import java.security.MessageDigest
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.json.Json

/** Kredensial disimpan terenkripsi (AES-GCM, Android Keystore) dan kode perangkat hanya sebagai hash SHA-256. */
class AndroidDeviceModeStore(context: Context) : DeviceModeStore {
    private val appContext = context.applicationContext
    private val prefs = appContext.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
    private val json = Json { ignoreUnknownKeys = true }

    override suspend fun load(): DeviceCredential? = withContext(Dispatchers.IO) {
        val raw = prefs.getString(KEY_CREDENTIAL, null) ?: return@withContext null
        runCatching { json.decodeFromString<DeviceCredential>(decrypt(raw)) }.getOrNull()
    }

    override suspend fun save(credential: DeviceCredential, code: String) {
        withContext(Dispatchers.IO) {
            prefs.edit()
                .putString(KEY_CREDENTIAL, encrypt(json.encodeToString(DeviceCredential.serializer(), credential)))
                .putString(KEY_CODE_HASH, hash(code))
                .commit()
        }
    }

    override suspend fun matches(code: String): Boolean = withContext(Dispatchers.IO) {
        prefs.getString(KEY_CODE_HASH, null) == hash(code)
    }

    override suspend fun markLinked(userName: String?, userToken: String?) {
        withContext(Dispatchers.IO) {
            val raw = prefs.getString(KEY_CREDENTIAL, null) ?: return@withContext
            val current = runCatching { json.decodeFromString<DeviceCredential>(decrypt(raw)) }.getOrNull()
                ?: return@withContext
            val updated = DeviceCredential(
                current.id, current.token, current.name, current.section,
                linked = true, userName = userName, userToken = userToken,
            )
            prefs.edit()
                .putString(KEY_CREDENTIAL, encrypt(json.encodeToString(DeviceCredential.serializer(), updated)))
                .commit()
        }
    }

    override suspend fun markUnlinked() {
        withContext(Dispatchers.IO) {
            val raw = prefs.getString(KEY_CREDENTIAL, null) ?: return@withContext
            val current = runCatching { json.decodeFromString<DeviceCredential>(decrypt(raw)) }.getOrNull()
                ?: return@withContext
            val updated = DeviceCredential(current.id, current.token, current.name, current.section)
            prefs.edit()
                .putString(KEY_CREDENTIAL, encrypt(json.encodeToString(DeviceCredential.serializer(), updated)))
                .commit()
        }
    }

    override suspend fun clear() {
        withContext(Dispatchers.IO) {
            prefs.edit().remove(KEY_CREDENTIAL).remove(KEY_CODE_HASH).remove(KEY_LAYOUT).commit()
        }
    }

    // Pilihan tampilan bukan rahasia, jadi disimpan tanpa enkripsi.
    override suspend fun layout(): String? = withContext(Dispatchers.IO) { prefs.getString(KEY_LAYOUT, null) }

    override suspend fun saveLayout(code: String) {
        withContext(Dispatchers.IO) {
            if (prefs.getString(KEY_LAYOUT, null) != code) prefs.edit().putString(KEY_LAYOUT, code).apply()
        }
    }

    /** Serial perangkat keras tidak bisa dibaca app biasa di Android 10 ke atas, jadi selalu null. */
    override fun deviceInfo(): DeviceInfo = DeviceInfo(
        androidId = Settings.Secure.getString(appContext.contentResolver, Settings.Secure.ANDROID_ID),
        serial = null,
        brand = Build.MANUFACTURER,
        model = Build.MODEL,
    )

    private fun hash(code: String): String =
        MessageDigest.getInstance("SHA-256")
            .digest(code.trim().toByteArray())
            .joinToString("") { "%02x".format(it) }

    private fun encrypt(plain: String): String {
        val cipher = Cipher.getInstance(TRANSFORMATION).apply { init(Cipher.ENCRYPT_MODE, secretKey()) }
        val payload = cipher.iv + cipher.doFinal(plain.toByteArray(Charsets.UTF_8))
        return Base64.encodeToString(payload, Base64.NO_WRAP)
    }

    private fun decrypt(encoded: String): String {
        val payload = Base64.decode(encoded, Base64.NO_WRAP)
        val iv = payload.copyOfRange(0, GCM_IV_BYTES)
        val cipher = Cipher.getInstance(TRANSFORMATION).apply {
            init(Cipher.DECRYPT_MODE, secretKey(), GCMParameterSpec(GCM_TAG_BITS, iv))
        }
        return String(cipher.doFinal(payload, GCM_IV_BYTES, payload.size - GCM_IV_BYTES), Charsets.UTF_8)
    }

    private fun secretKey(): SecretKey {
        val keyStore = KeyStore.getInstance(ANDROID_KEYSTORE).apply { load(null) }
        (keyStore.getKey(KEY_ALIAS, null) as? SecretKey)?.let { return it }

        val generator = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, ANDROID_KEYSTORE)
        generator.init(
            KeyGenParameterSpec.Builder(
                KEY_ALIAS,
                KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT,
            )
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setKeySize(256)
                .build(),
        )
        return generator.generateKey()
    }

    private companion object {
        const val PREFS_NAME = "device_mode"
        const val KEY_CREDENTIAL = "credential"
        const val KEY_CODE_HASH = "code_hash"
        const val KEY_LAYOUT = "layout"
        const val ANDROID_KEYSTORE = "AndroidKeyStore"
        const val KEY_ALIAS = "cafe_device_key"
        const val TRANSFORMATION = "AES/GCM/NoPadding"
        const val GCM_IV_BYTES = 12
        const val GCM_TAG_BITS = 128
    }
}
