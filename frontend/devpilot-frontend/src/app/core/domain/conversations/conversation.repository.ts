import { Observable } from 'rxjs';
import {
    Conversation,
    ConversationDetail,
} from '@core/domain/conversations/conversation.model';

export abstract class ConversationRepository {
    abstract getProjectConversations(
        projectId: string,
    ): Observable<readonly Conversation[]>;

    abstract getConversation(
        conversationId: string,
    ): Observable<ConversationDetail>;
}