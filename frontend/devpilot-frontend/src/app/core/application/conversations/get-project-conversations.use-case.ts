import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { Conversation } from '@core/domain/conversations/conversation.model';
import { ConversationRepository } from '@core/domain/conversations/conversation.repository';

@Injectable({
    providedIn: 'root',
})
export class GetProjectConversationsUseCase {
    private readonly conversationRepository = inject(
        ConversationRepository,
    );

    execute(
        projectId: string,
    ): Observable<readonly Conversation[]> {
        return this.conversationRepository.getProjectConversations(
            projectId,
        );
    }
}