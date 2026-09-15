export interface ProjectDocumentResponseDto {
    readonly id: string;
    readonly project_id: string;
    readonly path: string;
    readonly filename: string;
    readonly extension: string;
    readonly language: string;
    readonly size: number;
}

export interface GenerateUnitTestsRequestDto {
    readonly project_id: string;
    readonly document_id: string;
    readonly framework: string | null;
}

export interface UnitTestSourceResponseDto {
    readonly path: string;
    readonly language: string;
}

export interface GenerateUnitTestsResponseDto {
    readonly content: string;
    readonly suggested_filename: string;
    readonly sources: readonly UnitTestSourceResponseDto[];
}