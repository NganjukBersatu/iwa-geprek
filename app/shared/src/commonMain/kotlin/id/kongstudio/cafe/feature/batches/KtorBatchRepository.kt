package id.kongstudio.cafe.feature.batches

import id.kongstudio.cafe.core.network.ApiCaller
import id.kongstudio.cafe.core.network.ApiResult
import id.kongstudio.cafe.core.network.WriteResult
import id.kongstudio.cafe.core.network.appendFile
import id.kongstudio.cafe.core.network.multipart
import io.ktor.client.call.body
import io.ktor.http.HttpMethod
import kotlinx.serialization.builtins.ListSerializer
import kotlinx.serialization.json.Json

private const val BATCHES = "/v2/batches"
private const val ANSWERS_FIELD = "answers"
private const val FILES_FIELD = "files"

internal class KtorBatchRepository(private val api: ApiCaller) : BatchRepository {

    override suspend fun today(): ApiResult<List<Batch>> =
        api.read("$BATCHES/today") { it.body<BatchPageDto>().toModels() }

    override suspend fun complete(batchId: String, answers: List<BatchAnswer>): WriteResult<Batch> =
        sendAnswers(HttpMethod.Post, "$BATCHES/$batchId/complete", answers)

    override suspend fun stored(runId: String): ApiResult<StoredRun> =
        api.read("$BATCHES/runs/$runId") { it.body<StoredRunDto>().toModel(runId) }

    override suspend fun fix(runId: String, answers: List<BatchAnswer>): WriteResult<Batch> =
        sendAnswers(HttpMethod.Put, "$BATCHES/runs/$runId", answers)

    override suspend fun cancel(runId: String): WriteResult<Unit> =
        api.write(method = HttpMethod.Post, path = "$BATCHES/runs/$runId/cancel", configure = {}, parse = { })

    override suspend fun delete(runId: String): WriteResult<Unit> =
        api.write(method = HttpMethod.Delete, path = "$BATCHES/runs/$runId", configure = {}, parse = { })

    private suspend fun sendAnswers(method: HttpMethod, path: String, answers: List<BatchAnswer>): WriteResult<Batch> {
        val photos = answers.mapNotNull { it.photo }
        val dtos = answers.map { answer ->
            BatchAnswerDto(
                itemId = answer.itemId,
                value = answer.value,
                photoIndex = answer.photo?.let { photos.indexOf(it) },
                keepPhoto = answer.keepPhoto,
            )
        }
        return api.write(
            method = method,
            path = path,
            configure = {
                multipart {
                    append(ANSWERS_FIELD, Json.encodeToString(ListSerializer(BatchAnswerDto.serializer()), dtos))
                    photos.forEach { appendFile(FILES_FIELD, it.bytes, it.mimeType, it.fileName) }
                }
            },
            parse = { it.body<BatchDto>().toModel() },
        )
    }
}
