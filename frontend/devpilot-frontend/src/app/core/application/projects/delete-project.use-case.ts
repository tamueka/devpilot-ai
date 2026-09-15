import { inject, Injectable } from '@angular/core';
import { ProjectRepository } from '@core/domain/projects/project.repository';

@Injectable({
  providedIn: 'root',
})
export class DeleteProjectUseCase {
  private readonly projectRepository =
    inject(ProjectRepository);

  execute(
    projectId: string,
  ): Promise<void> {
    return this.projectRepository.deleteProject(
      projectId,
    );
  }
}