export interface ConversationResponseDto {
    readonly id: string;
    readonly project_id: string;
    readonly title: string | null;
    readonly created_at: string;
}

export interface ConversationMessageResponseDto {
    readonly id: string;
    readonly conversation_id: string;
    readonly role: 'user' | 'assistant';
    readonly content: string;
    readonly sources:
    | readonly ConversationSourceResponseDto[]
    | null;
    readonly created_at: string;
}

export interface ConversationSourceResponseDto {
    readonly path: string;
    readonly language: string;
    readonly chunk_index: number;
    readonly excerpt: string;
}

export interface ConversationDetailResponseDto
    extends ConversationResponseDto {
    readonly messages:
    readonly ConversationMessageResponseDto[];
}