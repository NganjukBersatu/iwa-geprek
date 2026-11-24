package id.kongstudio.cafe.feature.auth.session

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive

class AndroidSessionStore(context: Context) : SessionStore {
    private val prefs = context.applicationContext
        .getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
    private val json = Json { ignoreUnknownKeys = true }
    private val pendingLock = Any()

    override suspend fun load(): LoginSession? = withContext(Dispatchers.IO) {
        val raw = prefs.getString(KEY_SESSION, null) ?: return@withContext null
        val plain = runCatching { decrypt(raw) }.getOrNull()
        val stored = plain?.let { runCatching { json.decodeFromString<StoredSession>(it) }.getOrNull() }
        // Sesi tersimpan berbentuk lama tidak bisa dipakai lagi, jadi tokennya diantrekan untuk dicabut agar tidak tertinggal aktif di server.
        if (stored == null) plain?.let(::tokenOf)?.let { token -> synchronized(pendingLock) { writePending(readPending() + token) } }
        val expired = stored == null ||
            System.currentTimeMillis() - stored.savedAtMillis > stored.session.expiresInSeconds * 1000
        if (expired) {
            prefs.edit().remove(KEY_SESSION).apply()
            null
        } else {
            stored?.session
        }
    }

    override suspend fun save(session: LoginSession) = withContext(Dispatchers.IO) {
        val stored = StoredSession(session, System.currentTimeMillis())
        prefs.edit().putString(KEY_SESSION, encrypt(json.encodeToString(stored))).apply()
    }

    override suspend fun clear() = withContext(Dispatchers.IO) {
        prefs.edit().remove(KEY_SESSION).apply()
    }

    override suspend fun pendingRevocations(): List<String> = withContext(Dispatchers.IO) {
        synchronized(pendingLock) { readPending() }
    }

    override suspend fun addPendingRevocation(token: String) = withContext(Dispatchers.IO) {
        synchronized(pendingLock) { writePending(readPending() + token) }
    }

    override suspend fun removePendingRevocation(token: String) = withContext(Dispatchers.IO) {
        synchronized(pendingLock) { writePending(readPending() - token) }
    }

    private fun tokenOf(plain: String): String? = runCatching {
        json.parseToJsonElement(plain).jsonObject[KEY_STORED_SESSION]?.jsonObject?.get(KEY_ACCESS_TOKEN)?.jsonPrimitive?.content
    }.getOrNull()

    private fun readPending(): List<String> {
        val raw = prefs.getString(KEY_PENDING, null) ?: return emptyList()
        return runCatching { json.decodeFromString<List<String>>(decrypt(raw)) }.getOrDefault(emptyList())
    }

    private fun writePending(tokens: List<String>) {
        val edit = prefs.edit()
        if (tokens.isEmpty()) edit.remove(KEY_PENDING) else edit.putString(KEY_PENDING, encrypt(json.encodeToString(tokens.distinct())))
        edit.commit()
    }

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

    @Serializable
    private class StoredSession(val session: LoginSession, val savedAtMillis: Long)

    private companion object {
        const val PREFS_NAME = "session"
        const val KEY_SESSION = "login_session"
        const val KEY_PENDING = "pending_revocations"
        const val KEY_STORED_SESSION = "session"
        const val KEY_ACCESS_TOKEN = "accessToken"
        const val ANDROID_KEYSTORE = "AndroidKeyStore"
        const val KEY_ALIAS = "cafe_session_key"
        const val TRANSFORMATION = "AES/GCM/NoPadding"
        const val GCM_IV_BYTES = 12
        const val GCM_TAG_BITS = 128
    }
}
