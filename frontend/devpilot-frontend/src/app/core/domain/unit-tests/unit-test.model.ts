export interface ProjectDocument {
    readonly id: string;
    readonly projectId: string;
    readonly path: string;
    readonly filename: string;
    readonly extension: string;
    readonly language: string;
    readonly size: number;
}

export interface GenerateUnitTestsRequest {
    readonly projectId: string;
    readonly documentId: string;
    readonly framework?: string | null;
}

export interface UnitTestSource {
    readonly path: string;
    readonly language: string;
}

export interface GeneratedUnitTests {
    readonly content: string;
    readonly suggestedFilename: string;
    readonly sources: readonly UnitTestSource[];
}