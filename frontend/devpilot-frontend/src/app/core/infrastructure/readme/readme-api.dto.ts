export interface GenerateReadmeRequestDto {
    readonly project_id: string;
    readonly language: 'es' | 'en';
}

export interface ReadmeSourceResponseDto {
    readonly path: string;
    readonly language: string;
}

export interface GenerateReadmeResponseDto {
    readonly content: string;
    readonly sources: readonly ReadmeSourceResponseDto[];
}