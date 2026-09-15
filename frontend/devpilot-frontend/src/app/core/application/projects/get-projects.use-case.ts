import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { Project } from '@core/domain/projects/project.model';
import { ProjectRepository } from '@core/domain/projects/project.repository';

@Injectable({
    providedIn: 'root',
})
export class GetProjectsUseCase {
    private readonly projectRepository = inject(ProjectRepository);

    execute(): Observable<readonly Project[]> {
        return this.projectRepository.getProjects();
    }
}