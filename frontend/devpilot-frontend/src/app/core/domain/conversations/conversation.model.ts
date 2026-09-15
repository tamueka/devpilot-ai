import { ChatSource } from '@core/domain/chat/chat.model';

export interface Conversation {
    readonly id: string;
    readonly projectId: string;
    readonly title: string | null;
    readonly createdAt: string;
}

export interface ConversationMessage {
    readonly id: string;
    readonly conversationId: string;
    readonly role: 'user' | 'assistant';
    readonly content: string;
    readonly sources: readonly ChatSource[] | null;
    readonly createdAt: string;
}

export interface ConversationDetail extends Conversation {
    readonly messages: readonly ConversationMessage[];
}