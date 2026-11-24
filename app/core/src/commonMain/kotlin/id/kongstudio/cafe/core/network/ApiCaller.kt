package id.kongstudio.cafe.core.network

import id.kongstudio.cafe.core.failure.AppFailure
import id.kongstudio.cafe.core.failure.failureOf
import id.kongstudio.cafe.core.failure.unreadableAnswer
import io.ktor.client.HttpClient
import io.ktor.client.request.HttpRequestBuilder
import io.ktor.client.request.bearerAuth
import io.ktor.client.request.request
import io.ktor.client.request.setBody
import io.ktor.client.statement.HttpResponse
import io.ktor.client.statement.bodyAsText
import id.kongstudio.cafe.core.time.ServerClock
import io.ktor.http.ContentType
import io.ktor.http.HttpHeaders
import io.ktor.http.HttpMethod
import io.ktor.http.contentType
import kotlinx.coroutines.CancellationException

/** Hasil operasi yang mengubah data; sebab gagalnya, termasuk penolakan server, ada di [Failure]. */
sealed interface WriteResult<out T> {
    data class Success<T>(val value: T) : WriteResult<T>

    data object Unauthorized : WriteResult<Nothing>

    data class Failure(val failure: AppFailure) : WriteResult<Nothing>
}

/** Pemanggil API terautentikasi untuk satu sesi: membaca lewat [read], mengubah lewat [write]. */
class ApiCaller(
    private val client: HttpClient,
    baseUrl: String,
    private val accessToken: String,
) {
    private val base = baseUrl.trimEnd('/')

    suspend fun <T> read(
        path: String,
        configure: HttpRequestBuilder.() -> Unit = {},
        parse: suspend (HttpResponse) -> T?,
    ): ApiResult<T> {
        val where = "GET $path"
        val response = try {
            client.request("$base$path") {
                method = HttpMethod.Get
                bearerAuth(accessToken)
                configure()
            }
        } catch (e: CancellationException) {
            throw e
        } catch (e: Exception) {
            return ApiResult.Failure(failureOf(e, where))
        }
        ServerClock.sync(response.headers[HttpHeaders.Date])
        val code = response.status.value
        return when {
            code in 200..299 -> try {
                parse(response)?.let { ApiResult.Success(it) } ?: ApiResult.Failure(unreadableAnswer(code, where))
            } catch (e: CancellationException) {
                throw e
            } catch (e: Exception) {
                ApiResult.Failure(unreadableAnswer(code, where))
            }
            else -> failureOf(code, where, runCatching { response.bodyAsText() }.getOrNull()).toReadResult()
        }
    }

    suspend fun <T> write(
        method: HttpMethod,
        path: String,
        configure: HttpRequestBuilder.() -> Unit,
        parse: suspend (HttpResponse) -> T,
    ): WriteResult<T> {
        val where = "${method.value} $path"
        val response = try {
            client.request("$base$path") {
                this.method = method
                bearerAuth(accessToken)
                configure()
            }
        } catch (e: CancellationException) {
            throw e
        } catch (e: Exception) {
            return WriteResult.Failure(failureOf(e, where))
        }
        ServerClock.sync(response.headers[HttpHeaders.Date])
        val code = response.status.value
        return when {
            code in 200..299 -> try {
                WriteResult.Success(parse(response))
            } catch (e: CancellationException) {
                throw e
            } catch (e: Exception) {
                WriteResult.Failure(unreadableAnswer(code, where))
            }
            else -> failureOf(code, where, runCatching { response.bodyAsText() }.getOrNull()).toWriteResult()
        }
    }

    /** PUT berkas ke tautan unggah bertanda tangan (bukan API sendiri), tanpa token sesi. */
    suspend fun upload(url: String, contentType: String, bytes: ByteArray): WriteResult<Unit> {
        val where = "PUT unggah berkas"
        val response = try {
            client.request(url) {
                method = HttpMethod.Put
                contentType(ContentType.parse(contentType))
                setBody(bytes)
            }
        } catch (e: CancellationException) {
            throw e
        } catch (e: Exception) {
            return WriteResult.Failure(failureOf(e, where))
        }
        val code = response.status.value
        return if (code in 200..299) {
            WriteResult.Success(Unit)
        } else {
            failureOf(code, where, runCatching { response.bodyAsText() }.getOrNull()).toWriteResult()
        }
    }
}

private fun AppFailure.toReadResult(): ApiResult<Nothing> =
    if (this == AppFailure.Unauthorized) ApiResult.Unauthorized else ApiResult.Failure(this)

private fun AppFailure.toWriteResult(): WriteResult<Nothing> =
    if (this == AppFailure.Unauthorized) WriteResult.Unauthorized else WriteResult.Failure(this)
