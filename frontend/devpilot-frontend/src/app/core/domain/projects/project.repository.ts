import { ProjectArchive } from '@features/projects/project-archive.model';
import { Observable } from 'rxjs';
import { CreateProject, Project } from './project.model';

export abstract class ProjectRepository {
    abstract getProjects(): Observable<readonly Project[]>;
    abstract getProject(id: string): Observable<Project>;
    abstract createProject(project: CreateProject): Observable<Project>;
    abstract uploadArchive(
        projectId: string,
        archive: ProjectArchive,
    ): Observable<Project>;
    abstract deleteProject(
        projectId: string,
    ): Promise<void>;
}