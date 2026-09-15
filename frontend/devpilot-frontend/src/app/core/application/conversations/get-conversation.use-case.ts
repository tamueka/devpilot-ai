import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { ConversationDetail } from '@core/domain/conversations/conversation.model';
import { ConversationRepository } from '@core/domain/conversations/conversation.repository';

@Injectable({
    providedIn: 'root',
})
export class GetConversationUseCase {
    private readonly conversationRepository = inject(
        ConversationRepository,
    );

    execute(
        conversationId: string,
    ): Observable<ConversationDetail> {
        return this.conversationRepository.getConversation(
            conversationId,
        );
    }
}