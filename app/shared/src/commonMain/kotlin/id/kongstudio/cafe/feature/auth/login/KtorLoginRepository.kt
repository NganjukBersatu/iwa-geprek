package id.kongstudio.cafe.feature.auth.login

import id.kongstudio.cafe.core.failure.failureOf
import id.kongstudio.cafe.core.time.ServerClock
import io.ktor.client.HttpClient
import io.ktor.client.call.body
import io.ktor.client.request.post
import io.ktor.client.request.setBody
import io.ktor.client.statement.bodyAsText
import io.ktor.http.ContentType
import io.ktor.http.HttpHeaders
import io.ktor.http.HttpStatusCode
import io.ktor.http.contentType
import kotlinx.coroutines.CancellationException

private const val LoginPath = "/v2/auth/login"
private const val LoginCall = "POST $LoginPath"

class KtorLoginRepository(
    private val client: HttpClient,
    private val baseUrl: String,
) : LoginRepository {

    override suspend fun login(username: String, password: String): LoginResult = try {
        val response = client.post("${baseUrl.trimEnd('/')}$LoginPath") {
            contentType(ContentType.Application.Json)
            setBody(LoginRequestDto(username, password))
        }
        ServerClock.sync(response.headers[HttpHeaders.Date])
        when (response.status) {
            HttpStatusCode.OK -> LoginResult.Success(response.body<TokenResponseDto>().toSession())
            HttpStatusCode.Unauthorized -> LoginResult.InvalidCredentials
            HttpStatusCode.Forbidden -> LoginResult.AccountInactive
            else -> LoginResult.Failed(
                failureOf(response.status.value, LoginCall, runCatching { response.bodyAsText() }.getOrNull()),
            )
        }
    } catch (e: CancellationException) {
        throw e
    } catch (e: Exception) {
        LoginResult.Failed(failureOf(e, LoginCall))
    }
}
