import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, map } from 'rxjs';
import {
    Conversation,
    ConversationDetail,
} from '@core/domain/conversations/conversation.model';
import { ConversationRepository } from '@core/domain/conversations/conversation.repository';
import { environment } from '@env/environment';
import {
    ConversationDetailResponseDto,
    ConversationResponseDto,
} from './conversation-api.dto';

@Injectable()
export class ConversationApiRepository
    extends ConversationRepository {
    private readonly http = inject(HttpClient);
    private readonly apiUrl = environment.apiUrl;

    override getProjectConversations(
        projectId: string,
    ): Observable<readonly Conversation[]> {
        return this.http
            .get<readonly ConversationResponseDto[]>(
                `${this.apiUrl}/projects/${projectId}/conversations`,
            )
            .pipe(
                map((conversations) =>
                    conversations.map((conversation) =>
                        this.toConversationDomain(conversation),
                    ),
                ),
            );
    }

    override getConversation(
        conversationId: string,
    ): Observable<ConversationDetail> {
        return this.http
            .get<ConversationDetailResponseDto>(
                `${this.apiUrl}/conversations/${conversationId}`,
            )
            .pipe(
                map((conversation) =>
                    this.toConversationDetailDomain(conversation),
                ),
            );
    }

    private toConversationDomain(
        conversation: ConversationResponseDto,
    ): Conversation {
        return {
            id: conversation.id,
            projectId: conversation.project_id,
            title: conversation.title,
            createdAt: conversation.created_at,
        };
    }

    private toConversationDetailDomain(
        conversation: ConversationDetailResponseDto,
    ): ConversationDetail {
        return {
            ...this.toConversationDomain(conversation),

            messages: conversation.messages.map((message) => ({
                id: message.id,
                conversationId: message.conversation_id,
                role: message.role,
                content: message.content,
                createdAt: message.created_at,

                sources:
                    message.sources?.map((source) => ({
                        path: source.path,
                        language: source.language,
                        chunkIndex: source.chunk_index,
                        excerpt: source.excerpt,
                    })) ?? null,
            })),
        };
    }
}