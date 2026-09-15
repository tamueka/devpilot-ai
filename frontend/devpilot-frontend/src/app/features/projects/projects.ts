import { HttpErrorResponse } from '@angular/common/http';
import {
  Component,
  DestroyRef,
  OnInit,
  computed,
  inject,
  signal,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import {
  FormBuilder,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { RouterLink } from '@angular/router';
import { CreateProjectUseCase } from '@core/application/projects/create-project.use-case';
import { GetProjectsUseCase } from '@core/application/projects/get-projects.use-case';
import { UploadProjectArchiveUseCase } from '@core/application/projects/upload-project-archive.use-case';
import { GenerateReadmeUseCase } from '@core/application/readme/generate-readme.use-case';
import { GenerateUnitTestsUseCase } from '@core/application/unit-tests/generate-unit-tests.use-case';
import { GetProjectDocumentsUseCase } from '@core/application/unit-tests/get-project-documents.use-case';
import { DeleteProjectUseCase } from '@core/application/projects/delete-project.use-case';
import { Project } from '@core/domain/projects/project.model';
import { GeneratedReadme } from '@core/domain/readme/readme.model';
import {
  GeneratedUnitTests,
  ProjectDocument,
} from '@core/domain/unit-tests/unit-test.model';
import { marked } from 'marked';
import {
  finalize,
  from,
  switchMap,
  timer,
} from 'rxjs';

@Component({
  selector: 'app-projects',
  standalone: true,
  imports: [
    ReactiveFormsModule,
    RouterLink,
  ],
  templateUrl: './projects.html',
})
export class Projects implements OnInit {
  private readonly getProjectsUseCase = inject(
    GetProjectsUseCase,
  );
  private readonly createProjectUseCase = inject(
    CreateProjectUseCase,
  );
  private readonly uploadProjectArchiveUseCase = inject(
    UploadProjectArchiveUseCase,
  );
  private readonly deleteProjectUseCase =
    inject(DeleteProjectUseCase);
  private readonly generateReadmeUseCase = inject(
    GenerateReadmeUseCase,
  );
  private readonly getProjectDocumentsUseCase = inject(
    GetProjectDocumentsUseCase,
  );

  private readonly generateUnitTestsUseCase = inject(
    GenerateUnitTestsUseCase,
  );
  private readonly fb = inject(FormBuilder);
  private readonly destroyRef = inject(DestroyRef);
  readonly projects = signal<readonly Project[]>([]);
  readonly loading = signal(false);
  readonly creating = signal(false);
  readonly uploadingProjectId = signal<string | null>(null);
  readonly uploadErrorProjectId =
    signal<string | null>(null);
  readonly uploadError =
    signal<string | null>(null);
  readonly uploadSuccessProjectId =
    signal<string | null>(null);
  readonly uploadSuccess =
    signal<string | null>(null);
  readonly generatingReadmeProjectId =
    signal<string | null>(null);
  readonly generatedReadme =
    signal<GeneratedReadme | null>(null);
  readonly readmeProjectName =
    signal<string | null>(null);
  readonly showReadme =
    signal(false);
  readonly unitTestDocuments =
    signal<readonly ProjectDocument[]>([]);
  readonly selectedUnitTestProjectId =
    signal<string | null>(null);
  readonly selectedUnitTestDocumentId =
    signal<string | null>(null);
  readonly generatedUnitTests =
    signal<GeneratedUnitTests | null>(null);
  readonly loadingUnitTestDocuments =
    signal(false);
  readonly generatingUnitTests =
    signal(false);
  readonly showUnitTests =
    signal(false);
  readonly error = signal<string | null>(null);
  readonly openProjectMenuId =
    signal<string | null>(null);
  readonly projectToDelete =
    signal<Project | null>(null);
  readonly deletingProjectId =
    signal<string | null>(null);
  readonly deleteProjectError =
    signal<string | null>(null);
  readonly deleteProjectSuccess =
    signal<string | null>(null);

  readonly projectForm = this.fb.nonNullable.group({
    name: [
      '',
      [
        Validators.required,
        Validators.maxLength(200),
      ],
    ],
    description: [
      '',
      [
        Validators.maxLength(1000),
      ],
    ],
  });

  ngOnInit(): void {
    this.loadProjects();
  }

  loadProjects(): void {
    this.loading.set(true);
    this.error.set(null);

    this.getProjectsUseCase
      .execute()
      .pipe(
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe({
        next: (projects) => {
          this.projects.set(projects);
          this.loading.set(false);
        },
        error: (error: HttpErrorResponse) => {
          console.error(
            'Error cargando proyectos:',
            error,
          );

          this.error.set(
            'No se pudieron cargar los proyectos.',
          );

          this.loading.set(false);
        },
      });
  }

  createProject(): void {
    if (this.projectForm.invalid) {
      this.projectForm.markAllAsTouched();
      return;
    }

    this.creating.set(true);
    this.error.set(null);

    const projectData = this.projectForm.getRawValue();

    this.createProjectUseCase
      .execute(projectData)
      .pipe(
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe({
        next: (project) => {
          this.projects.update(
            (projects) => [
              project,
              ...projects,
            ],
          );

          this.projectForm.reset({
            name: '',
            description: '',
          });

          this.creating.set(false);
        },
        error: (error: HttpErrorResponse) => {
          console.error(
            'Error creando proyecto:',
            error,
          );

          this.error.set(
            'No se pudo crear el proyecto.',
          );

          this.creating.set(false);
        },
      });
  }

  uploadArchive(
    projectId: string,
    event: Event,
  ): void {
    const input =
      event.target as HTMLInputElement;

    const file =
      input.files?.[0];

    if (!file) {
      return;
    }

    this.uploadError.set(null);
    this.uploadErrorProjectId.set(null);
    this.uploadSuccess.set(null);
    this.uploadSuccessProjectId.set(null);

    const extension =
      file.name
        .toLowerCase()
        .split('.')
        .at(-1);

    if (
      extension !== 'zip' &&
      extension !== 'rar'
    ) {
      this.uploadErrorProjectId.set(
        projectId,
      );

      this.uploadError.set(
        'El archivo seleccionado debe ser '
        + 'un archivo .zip o .rar.',
      );

      input.value = '';
      return;
    }

    this.uploadingProjectId.set(
      projectId,
    );

    from(file.arrayBuffer())
      .pipe(
        switchMap((content) =>
          this.uploadProjectArchiveUseCase.execute(
            projectId,
            {
              filename: file.name,
              mimeType: file.type,
              content,
            },
          ),
        ),
        finalize(() => {
          this.uploadingProjectId.set(
            null,
          );

          input.value = '';
        }),
        takeUntilDestroyed(
          this.destroyRef,
        ),
      )
      .subscribe({
        next: (updatedProject) => {
          this.projects.update(
            (projects) =>
              projects.map(
                (project) =>
                  project.id === updatedProject.id
                    ? updatedProject
                    : project,
              ),
          );

          this.uploadError.set(null);
          this.uploadErrorProjectId.set(null);
          this.uploadSuccessProjectId.set(
            projectId,
          );
          this.uploadSuccess.set(
            `Archivo "${file.name}" indexado correctamente.`,
          );
          timer(4_000)
            .pipe(
              takeUntilDestroyed(
                this.destroyRef,
              ),
            )
            .subscribe(() => {
              if (
                this.uploadSuccessProjectId()
                === projectId
              ) {
                this.uploadSuccess.set(null);
                this.uploadSuccessProjectId.set(
                  null,
                );
              }
            });
        },

        error: (
          error: HttpErrorResponse,
        ) => {
          console.error(
            'Error subiendo el proyecto:',
            error,
          );

          this.uploadErrorProjectId.set(
            projectId,
          );

          this.uploadError.set(
            this.getUploadErrorMessage(
              error,
            ),
          );
        },
      });
  }

  private getUploadErrorMessage(
    error: HttpErrorResponse,
  ): string {
    const detail =
      error.error?.detail;

    if (
      typeof detail === 'string' &&
      detail.trim()
    ) {
      return detail;
    }

    if (error.status === 413) {
      return (
        'El archivo supera el tamaño '
        + 'máximo permitido de 50 MB.'
      );
    }

    if (error.status === 400) {
      return (
        'El archivo ZIP o RAR no es válido '
        + 'o no se puede procesar.'
      );
    }

    if (error.status === 0) {
      return (
        'No se pudo conectar con el servidor. '
        + 'Comprueba que el backend está iniciado.'
      );
    }

    return (
      'No se pudo subir e indexar '
      + 'el proyecto.'
    );
  }

  getStatusLabel(
    project: Project,
  ): string {
    if (this.uploadingProjectId() === project.id) {
      return 'Indexando';
    }

    switch (project.status) {
      case 'INDEXED':
        return 'Indexado';

      case 'CREATED':
        return 'Pendiente';

      case 'UPLOADED':
      case 'EXTRACTED':
      case 'INDEXED_FILES':
      case 'CHUNKED':
        return 'Procesando';

      default:
        return project.status;
    }
  }

  getUploadedFileName(
    project: Project,
  ): string | null {
    const uploadedFile =
      project.uploaded_file?.trim();

    if (!uploadedFile) {
      return null;
    }

    return (
      uploadedFile
        .replace(/\\/g, '/')
        .split('/')
        .at(-1)
      ?? null
    );
  }

  readonly formattedReadme = computed(() => {
    const content =
      this.generatedReadme()?.content;

    if (!content) {
      return '';
    }

    return marked.parse(content, {
      async: false,
    });
  });

  generateReadme(
    project: Project,
  ): void {
    if (
      project.status !== 'INDEXED' ||
      this.generatingReadmeProjectId()
    ) {
      return;
    }

    this.generatingReadmeProjectId.set(
      project.id,
    );

    this.generatedReadme.set(null);
    this.readmeProjectName.set(project.name);
    this.showReadme.set(true);
    this.error.set(null);

    this.generateReadmeUseCase
      .execute({
        projectId: project.id,
        language: 'es',
      })
      .pipe(
        finalize(() => {
          this.generatingReadmeProjectId.set(
            null,
          );
        }),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe({
        next: (readme) => {
          this.generatedReadme.set(
            readme,
          );
        },

        error: (error: HttpErrorResponse) => {
          console.error(
            'Error generando README:',
            error,
          );

          this.showReadme.set(false);

          this.error.set(
            typeof error.error?.detail ===
              'string'
              ? error.error.detail
              : 'No se pudo generar el README.',
          );
        },
      });
  }

  async copyReadme(): Promise<void> {
    const content =
      this.generatedReadme()?.content;

    if (!content) {
      return;
    }

    await navigator.clipboard.writeText(
      content,
    );
  }

  downloadReadme(): void {
    const content =
      this.generatedReadme()?.content;

    if (!content) {
      return;
    }

    const blob = new Blob(
      [content],
      {
        type: 'text/markdown;charset=utf-8',
      },
    );

    const url =
      URL.createObjectURL(blob);

    const link =
      document.createElement('a');

    link.href = url;
    link.download = 'README.md';

    document.body.appendChild(link);
    link.click();
    link.remove();

    URL.revokeObjectURL(url);
  }

  closeReadme(): void {
    this.showReadme.set(false);
    this.generatedReadme.set(null);
    this.readmeProjectName.set(null);
  }

  openUnitTests(
    project: Project,
  ): void {
    if (project.status !== 'INDEXED') {
      return;
    }

    this.selectedUnitTestProjectId.set(
      project.id,
    );

    this.selectedUnitTestDocumentId.set(
      null,
    );

    this.unitTestDocuments.set([]);
    this.generatedUnitTests.set(null);
    this.showUnitTests.set(true);
    this.error.set(null);

    this.loadUnitTestDocuments(
      project.id,
    );
  }

  private loadUnitTestDocuments(
    projectId: string,
  ): void {
    this.loadingUnitTestDocuments.set(
      true,
    );

    this.getProjectDocumentsUseCase
      .execute(projectId)
      .pipe(
        finalize(() => {
          this.loadingUnitTestDocuments.set(
            false,
          );
        }),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe({
        next: (documents) => {
          this.unitTestDocuments.set(
            documents,
          );
        },

        error: (error: HttpErrorResponse) => {
          console.error(
            'Error cargando archivos:',
            error,
          );

          this.error.set(
            typeof error.error?.detail ===
              'string'
              ? error.error.detail
              : 'No se pudieron cargar los archivos del proyecto.',
          );

          this.showUnitTests.set(false);
        },
      });
  }

  selectUnitTestDocument(
    documentId: string,
  ): void {
    this.selectedUnitTestDocumentId.set(
      documentId || null,
    );

    this.generatedUnitTests.set(null);
  }

  generateUnitTests(): void {
    const projectId =
      this.selectedUnitTestProjectId();

    const documentId =
      this.selectedUnitTestDocumentId();

    if (
      !projectId ||
      !documentId ||
      this.generatingUnitTests()
    ) {
      return;
    }

    this.generatingUnitTests.set(true);
    this.generatedUnitTests.set(null);
    this.error.set(null);

    this.generateUnitTestsUseCase
      .execute({
        projectId,
        documentId,
        framework: null,
      })
      .pipe(
        finalize(() => {
          this.generatingUnitTests.set(
            false,
          );
        }),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe({
        next: (unitTests) => {
          this.generatedUnitTests.set(
            unitTests,
          );
        },

        error: (error: HttpErrorResponse) => {
          console.error(
            'Error generando tests:',
            error,
          );

          this.error.set(
            typeof error.error?.detail ===
              'string'
              ? error.error.detail
              : 'No se pudieron generar los tests unitarios.',
          );
        },
      });
  }

  closeUnitTests(): void {
    this.showUnitTests.set(false);
    this.unitTestDocuments.set([]);
    this.selectedUnitTestProjectId.set(
      null,
    );
    this.selectedUnitTestDocumentId.set(
      null,
    );
    this.generatedUnitTests.set(null);
  }

  async copyUnitTests(): Promise<void> {
    const content =
      this.generatedUnitTests()?.content;

    if (!content) {
      return;
    }

    await navigator.clipboard.writeText(
      content,
    );
  }

  downloadUnitTests(): void {
    const unitTests =
      this.generatedUnitTests();

    if (!unitTests) {
      return;
    }

    const blob = new Blob(
      [unitTests.content],
      {
        type: 'text/plain;charset=utf-8',
      },
    );

    const url =
      URL.createObjectURL(blob);

    const link =
      document.createElement('a');

    link.href = url;
    link.download =
      unitTests.suggestedFilename;

    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  getArchiveLabel(
    project: Project,
  ): string {
    const filename =
      this.getUploadedFileName(project);

    if (!filename) {
      return 'FILE';
    }

    const extension =
      filename
        .split('.')
        .at(-1)
        ?.toUpperCase();

    return extension === 'RAR'
      ? 'RAR'
      : 'ZIP';
  }

  toggleProjectMenu(
    projectId: string,
  ): void {
    this.openProjectMenuId.update(
      (currentId) =>
        currentId === projectId
          ? null
          : projectId,
    );
  }


  requestProjectDeletion(
    project: Project,
  ): void {
    this.openProjectMenuId.set(null);

    this.deleteProjectError.set(null);

    this.projectToDelete.set(
      project,
    );
  }


  cancelProjectDeletion(): void {
    if (this.deletingProjectId()) {
      return;
    }

    this.projectToDelete.set(null);
    this.deleteProjectError.set(null);
  }


  async confirmProjectDeletion(): Promise<void> {
    const project =
      this.projectToDelete();

    if (
      !project ||
      this.deletingProjectId()
    ) {
      return;
    }

    this.deletingProjectId.set(
      project.id,
    );

    this.deleteProjectError.set(null);
    this.deleteProjectSuccess.set(null);

    try {
      await this.deleteProjectUseCase.execute(
        project.id,
      );

      this.projects.update(
        (projects) =>
          projects.filter(
            (currentProject) =>
              currentProject.id !==
              project.id,
          ),
      );

      this.projectToDelete.set(null);

      this.deleteProjectSuccess.set(
        `Proyecto "${project.name}" eliminado correctamente.`,
      );

      setTimeout(
        () => {
          if (
            this.deleteProjectSuccess()
          ) {
            this.deleteProjectSuccess.set(
              null,
            );
          }
        },
        4_000,
      );
    } catch (error) {
      console.error(
        'Error eliminando proyecto:',
        error,
      );

      this.deleteProjectError.set(
        'No se pudo eliminar el proyecto. '
        + 'Inténtalo de nuevo.',
      );
    } finally {
      this.deletingProjectId.set(null);
    }
  }
}