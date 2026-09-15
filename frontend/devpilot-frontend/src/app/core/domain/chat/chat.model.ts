export interface ChatRequest {
    readonly projectId: string;
    readonly conversationId?: string | null;
    readonly message: string;
    readonly topK?: number;
}

export interface ChatSource {
    readonly path: string;
    readonly language: string;
    readonly chunkIndex: number;
    readonly excerpt: string;
}

export interface ChatResponse {
    readonly conversationId: string;
    readonly answer: string;
    readonly sources: readonly ChatSource[];
}