import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, map } from 'rxjs';
import {
    ChatRequest,
    ChatResponse,
} from '@core/domain/chat/chat.model';
import { ChatRepository } from '@core/domain/chat/chat.repository';
import { environment } from '@env/environment';
import {
    ChatRequestDto,
    ChatResponseDto,
} from './chat-api.dto';

@Injectable()
export class ChatApiRepository extends ChatRepository {
    private readonly http = inject(HttpClient);
    private readonly apiUrl = environment.apiUrl;

    override ask(
        request: ChatRequest,
    ): Observable<ChatResponse> {
        const requestDto = this.toRequestDto(
            request,
        );

        return this.http
            .post<ChatResponseDto>(
                `${this.apiUrl}/chat`,
                requestDto,
            )
            .pipe(
                map(
                    (response) =>
                        this.toDomain(response),
                ),
            );
    }

    private toRequestDto(
        request: ChatRequest,
    ): ChatRequestDto {
        return {
            project_id: request.projectId,
            message: request.message,

            ...(request.conversationId !== undefined
                ? {
                    conversation_id:
                        request.conversationId,
                }
                : {}),

            ...(request.topK !== undefined
                ? {
                    top_k: request.topK,
                }
                : {}),
        };
    }

    private toDomain(
        response: ChatResponseDto,
    ): ChatResponse {
        return {
            conversationId:
                response.conversation_id,

            answer: response.answer,

            sources: response.sources.map(
                (source) => ({
                    path: source.path,
                    language: source.language,
                    chunkIndex:
                        source.chunk_index,
                    excerpt: source.excerpt,
                }),
            ),
        };
    }
}