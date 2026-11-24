package id.kongstudio.cafe.feature.devicesetup

import id.kongstudio.cafe.core.failure.AppFailure
import id.kongstudio.cafe.core.failure.failureOf
import id.kongstudio.cafe.core.failure.unreadableAnswer
import io.ktor.client.HttpClient
import io.ktor.client.request.HttpRequestBuilder
import io.ktor.client.request.bearerAuth
import io.ktor.client.request.request
import io.ktor.client.statement.HttpResponse
import io.ktor.client.statement.bodyAsText
import io.ktor.http.HttpMethod
import kotlinx.coroutines.CancellationException

sealed interface DeviceResult<out T> {
    data class Ok<T>(val value: T) : DeviceResult<T>

    data class Failed(val failure: AppFailure) : DeviceResult<Nothing>
}

internal inline fun <T, R> DeviceResult<T>.map(transform: (T) -> R): DeviceResult<R> = when (this) {
    is DeviceResult.Ok -> DeviceResult.Ok(transform(value))
    is DeviceResult.Failed -> this
}

/** Satu panggilan HTTP yang membedakan penyebab gagalnya; [bearer] boleh null untuk endpoint publik. */
internal suspend fun <T> deviceCall(
    client: HttpClient,
    baseUrl: String,
    method: HttpMethod,
    path: String,
    bearer: String? = null,
    configure: HttpRequestBuilder.() -> Unit = {},
    parse: suspend (HttpResponse) -> T,
): DeviceResult<T> {
    val where = "${method.value} $path"
    val response = try {
        client.request("${baseUrl.trimEnd('/')}$path") {
            this.method = method
            bearer?.let { bearerAuth(it) }
            configure()
        }
    } catch (e: CancellationException) {
        throw e
    } catch (e: Exception) {
        return DeviceResult.Failed(failureOf(e, where))
    }

    val code = response.status.value
    return when {
        code in 200..299 -> try {
            DeviceResult.Ok(parse(response))
        } catch (e: CancellationException) {
            throw e
        } catch (e: Exception) {
            DeviceResult.Failed(unreadableAnswer(code, where))
        }
        else -> DeviceResult.Failed(failureOf(code, where, runCatching { response.bodyAsText() }.getOrNull()))
    }
}
