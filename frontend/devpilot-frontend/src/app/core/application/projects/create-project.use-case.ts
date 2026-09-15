import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
    CreateProject,
    Project,
} from '@core/domain/projects/project.model';
import { ProjectRepository } from '@core/domain/projects/project.repository';

@Injectable({
    providedIn: 'root',
})
export class CreateProjectUseCase {
    private readonly projectRepository = inject(ProjectRepository);

    execute(project: CreateProject): Observable<Project> {
        return this.projectRepository.createProject(project);
    }
}