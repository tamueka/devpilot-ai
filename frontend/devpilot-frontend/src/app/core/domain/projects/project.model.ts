export interface Project {
    readonly id: string;
    readonly name: string;
    readonly description: string | null;
    readonly status: string;
    readonly uploaded_file: string | null;
    readonly created_at: string;
    readonly updated_at: string;
}

export interface CreateProject {
    readonly name: string;
    readonly description?: string | null;
} 