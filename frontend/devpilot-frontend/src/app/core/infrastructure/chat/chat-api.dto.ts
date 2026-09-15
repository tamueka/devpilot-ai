export interface ChatRequestDto {
  readonly project_id: string;
  readonly conversation_id?: string | null;
  readonly message: string;
  readonly top_k?: number;
}

export interface ChatSourceResponseDto {
  readonly path: string;
  readonly language: string;
  readonly chunk_index: number;
  readonly excerpt: string;
}

export interface ChatResponseDto {
  readonly conversation_id: string;
  readonly answer: string;
  readonly sources: readonly ChatSourceResponseDto[];
}