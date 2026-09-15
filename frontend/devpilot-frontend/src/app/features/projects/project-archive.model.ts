export interface ProjectArchive {
    readonly filename: string;
    readonly mimeType: string;
    readonly content: ArrayBuffer;
}