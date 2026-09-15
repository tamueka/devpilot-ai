import { Observable } from 'rxjs';

import { ProjectArchive } from '@features/projects/project-archive.model';
import {
  CreateProject,
  Project,
} from '@core/domain/projects/project.model';

export abstract class ProjectRepository {
  abstract getProjects(): Observable<readonly Project[]>;

  abstract getProject(id: string): Observable<Project>;

  abstract createProject(
    project: CreateProject,
  ): Observable<Project>;

  abstract uploadArchive(
    projectId: string,
    archive: ProjectArchive,
  ): Observable<Project>;
}