import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { firstValueFrom, Observable } from 'rxjs';
import { ProjectArchive } from '@features/projects/project-archive.model';
import {
    CreateProject,
    Project,
} from '@core/domain/projects/project.model';
import { ProjectRepository } from '@core/domain/projects/project.repository';
import { environment } from '@env/environment';

@Injectable({
    providedIn: 'root',
})
export class ProjectApiRepository extends ProjectRepository {
    private readonly http = inject(HttpClient);
    private readonly apiUrl = environment.apiUrl;

    override getProjects(): Observable<readonly Project[]> {
        return this.http.get<readonly Project[]>(
            `${this.apiUrl}/projects`,
        );
    }

    override getProject(
        id: string,
    ): Observable<Project> {
        return this.http.get<Project>(
            `${this.apiUrl}/projects/${id}`,
        );
    }

    override createProject(
        project: CreateProject,
    ): Observable<Project> {
        return this.http.post<Project>(
            `${this.apiUrl}/projects`,
            project,
        );
    }

    override uploadArchive(
        projectId: string,
        archive: ProjectArchive,
    ): Observable<Project> {
        const formData = new FormData();

        const fileBlob = new Blob(
            [archive.content],
            {
                type: archive.mimeType || 'application/zip',
            },
        );

        formData.append(
            'file',
            fileBlob,
            archive.filename,
        );

        return this.http.post<Project>(
            `${this.apiUrl}/projects/${projectId}/upload`,
            formData,
        );
    }

    async deleteProject(
        projectId: string,
    ): Promise<void> {
        await firstValueFrom(
            this.http.delete<void>(
                `${environment.apiUrl}/projects/${projectId}`,
            ),
        );
    }
}