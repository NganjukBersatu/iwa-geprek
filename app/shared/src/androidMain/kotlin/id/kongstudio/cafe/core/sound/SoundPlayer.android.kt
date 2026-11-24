package id.kongstudio.cafe.core.sound

import android.content.Context
import android.media.AudioAttributes
import android.media.MediaPlayer
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.platform.LocalContext
import id.kongstudio.cafe.resources.Res
import java.io.File
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

@Composable
actual fun rememberSoundPlayer(): SoundPlayer {
    val context = LocalContext.current.applicationContext
    val scope = rememberCoroutineScope()
    return remember(context, scope) { AndroidSoundPlayer(context, scope) }
}

private class AndroidSoundPlayer(private val context: Context, private val scope: CoroutineScope) : SoundPlayer {
    override fun play(sound: AppSound) {
        scope.launch {
            val file = runCatching { withContext(Dispatchers.IO) { cached(sound) } }.getOrNull() ?: return@launch
            val player = runCatching { MediaPlayer() }.getOrNull() ?: return@launch
            // Gagal di tengah persiapan pun pemutarnya tetap dilepas, supaya suara yang gagal tidak menumpuk memori.
            runCatching {
                player.setOnCompletionListener { it.release() }
                player.setOnErrorListener { failed, _, _ ->
                    failed.release()
                    true
                }
                if (sound.alarm) {
                    player.setAudioAttributes(
                        AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_ALARM).setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION).build(),
                    )
                }
                player.setDataSource(file.path)
                player.prepare()
                player.start()
            }.onFailure { runCatching { player.release() } }
        }
    }

    /** MediaPlayer memutar dari berkas, jadi suara dari resource disalin sekali ke cache aplikasi. */
    private suspend fun cached(sound: AppSound): File {
        val file = File(context.cacheDir, "sounds/${sound.path.substringAfterLast('/')}")
        if (!file.exists()) {
            file.parentFile?.mkdirs()
            // Ditulis utuh dulu baru dipindah, supaya salinan yang terputus tidak tertinggal sebagai berkas rusak selamanya.
            val partial = File(file.parentFile, "${file.name}.part")
            partial.writeBytes(Res.readBytes(sound.path))
            if (!partial.renameTo(file)) partial.delete()
        }
        return file
    }
}
