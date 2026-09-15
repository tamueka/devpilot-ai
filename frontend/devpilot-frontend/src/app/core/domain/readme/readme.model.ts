export type ReadmeLanguage = 'es' | 'en';

export interface GenerateReadmeRequest {
    readonly projectId: string;
    readonly language: ReadmeLanguage;
}

export interface ReadmeSource {
    readonly path: string;
    readonly language: string;
}

export interface GeneratedReadme {
    readonly content: string;
    readonly sources: readonly ReadmeSource[];
}