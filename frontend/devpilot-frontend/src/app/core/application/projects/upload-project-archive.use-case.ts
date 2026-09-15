import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { ProjectArchive } from '@features/projects/project-archive.model';
import { Project } from '@core/domain/projects/project.model';
import { ProjectRepository } from '@core/domain/projects/project.repository';

@Injectable({
  providedIn: 'root',
})
export class UploadProjectArchiveUseCase {
  private readonly projectRepository = inject(ProjectRepository);

  execute(
    projectId: string,
    archive: ProjectArchive,
  ): Observable<Project> {
    return this.projectRepository.uploadArchive(
      projectId,
      archive,
    );
  }
}