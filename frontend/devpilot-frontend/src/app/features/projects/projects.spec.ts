import { HttpErrorResponse } from '@angular/common/http';
import {
    ComponentFixture,
    TestBed,
} from '@angular/core/testing';
import {
    provideRouter,
} from '@angular/router';
import { CreateProjectUseCase } from '@core/application/projects/create-project.use-case';
import { DeleteProjectUseCase } from '@core/application/projects/delete-project.use-case';
import { GetProjectsUseCase } from '@core/application/projects/get-projects.use-case';
import { UploadProjectArchiveUseCase } from '@core/application/projects/upload-project-archive.use-case';
import { GenerateReadmeUseCase } from '@core/application/readme/generate-readme.use-case';
import { GenerateUnitTestsUseCase } from '@core/application/unit-tests/generate-unit-tests.use-case';
import { GetProjectDocumentsUseCase } from '@core/application/unit-tests/get-project-documents.use-case';
import { Project } from '@core/domain/projects/project.model';
import { GeneratedReadme } from '@core/domain/readme/readme.model';
import {
    GeneratedUnitTests,
    ProjectDocument,
} from '@core/domain/unit-tests/unit-test.model';
import {
    of,
    throwError,
} from 'rxjs';
import { vi } from 'vitest';

import { Projects } from './projects';


describe('Projects', () => {
    let fixture: ComponentFixture<Projects>;
    let component: Projects;

    const getProjectsUseCaseMock = {
        execute: vi.fn(),
    };

    const createProjectUseCaseMock = {
        execute: vi.fn(),
    };

    const uploadProjectArchiveUseCaseMock = {
        execute: vi.fn(),
    };

    const generateReadmeUseCaseMock = {
        execute: vi.fn(),
    };

    const getProjectDocumentsUseCaseMock = {
        execute: vi.fn(),
    };

    const generateUnitTestsUseCaseMock = {
        execute: vi.fn(),
    };

    const deleteProjectUseCaseMock = {
        execute: vi.fn(),
    };


    const createdProject = {
        id: 'project-1',
        name: 'DevPilot',
        description: 'Proyecto DevPilot',
        status: 'CREATED',
        uploaded_file: null,
    } as Project;


    const indexedProject = {
        id: 'project-2',
        name: 'Angular Ecommerce',
        description: 'Proyecto Angular',
        status: 'INDEXED',
        uploaded_file:
            'storage/projects/project-2/ecommerce.zip',
    } as Project;


    const indexedUpdatedProject = {
        ...createdProject,
        status: 'INDEXED',
        uploaded_file:
            'storage/projects/project-1/devpilot.zip',
    } as Project;


    const generatedReadme: GeneratedReadme = {
        content:
            '# DevPilot AI\n\nAsistente para analizar código.',

        sources: [
            {
                path: 'src/app/app.ts',
                language: 'typescript',
            },
            {
                path: 'package.json',
                language: 'json',
            },
        ],
    };


    const projectDocuments:
        readonly ProjectDocument[] = [
            {
                id: 'document-1',
                projectId: 'project-2',
                path: 'src/app/app.ts',
                filename: 'app.ts',
                extension: '.ts',
                language: 'typescript',
                size: 200,
            },
            {
                id: 'document-2',
                projectId: 'project-2',
                path: 'src/app/app.config.ts',
                filename: 'app.config.ts',
                extension: '.ts',
                language: 'typescript',
                size: 300,
            },
        ];


    const generatedUnitTests:
        GeneratedUnitTests = {
        content: [
            "describe('App', () => {",
            "  it('should work', () => {",
            '    expect(true).toBe(true);',
            '  });',
            '});',
        ].join('\n'),

        suggestedFilename:
            'app.spec.ts',

        sources: [
            {
                path: 'src/app/app.ts',
                language: 'typescript',
            },
        ],
    };


    beforeEach(async () => {
        getProjectsUseCaseMock.execute.mockReset();

        createProjectUseCaseMock.execute.mockReset();

        uploadProjectArchiveUseCaseMock
            .execute
            .mockReset();

        generateReadmeUseCaseMock.execute.mockReset();

        getProjectDocumentsUseCaseMock
            .execute
            .mockReset();

        generateUnitTestsUseCaseMock
            .execute
            .mockReset();

        deleteProjectUseCaseMock
            .execute
            .mockReset();


        getProjectsUseCaseMock.execute.mockReturnValue(
            of([]),
        );

        createProjectUseCaseMock.execute.mockReturnValue(
            of(createdProject),
        );

        uploadProjectArchiveUseCaseMock
            .execute
            .mockReturnValue(
                of(indexedUpdatedProject),
            );

        generateReadmeUseCaseMock
            .execute
            .mockReturnValue(
                of(generatedReadme),
            );

        getProjectDocumentsUseCaseMock
            .execute
            .mockReturnValue(
                of(projectDocuments),
            );

        generateUnitTestsUseCaseMock
            .execute
            .mockReturnValue(
                of(generatedUnitTests),
            );

        deleteProjectUseCaseMock
            .execute
            .mockResolvedValue(
                undefined,
            );


        await TestBed.configureTestingModule({
            imports: [
                Projects,
            ],

            providers: [
                provideRouter([]),

                {
                    provide:
                        GetProjectsUseCase,

                    useValue:
                        getProjectsUseCaseMock,
                },

                {
                    provide:
                        CreateProjectUseCase,

                    useValue:
                        createProjectUseCaseMock,
                },

                {
                    provide:
                        UploadProjectArchiveUseCase,

                    useValue:
                        uploadProjectArchiveUseCaseMock,
                },

                {
                    provide:
                        GenerateReadmeUseCase,

                    useValue:
                        generateReadmeUseCaseMock,
                },

                {
                    provide:
                        GetProjectDocumentsUseCase,

                    useValue:
                        getProjectDocumentsUseCaseMock,
                },

                {
                    provide:
                        GenerateUnitTestsUseCase,

                    useValue:
                        generateUnitTestsUseCaseMock,
                },

                {
                    provide:
                        DeleteProjectUseCase,

                    useValue:
                        deleteProjectUseCaseMock,
                },
            ],
        }).compileComponents();
    });


    afterEach(() => {
        vi.useRealTimers();
        vi.restoreAllMocks();
    });


    function createComponent(): void {
        fixture =
            TestBed.createComponent(
                Projects,
            );

        component =
            fixture.componentInstance;

        fixture.detectChanges();
    }


    it(
        'should create and load projects',
        () => {
            getProjectsUseCaseMock
                .execute
                .mockReturnValue(
                    of([
                        createdProject,
                        indexedProject,
                    ]),
                );

            createComponent();

            expect(
                component,
            ).toBeTruthy();

            expect(
                getProjectsUseCaseMock.execute,
            ).toHaveBeenCalledOnce();

            expect(
                component.projects(),
            ).toEqual([
                createdProject,
                indexedProject,
            ]);

            expect(
                component.loading(),
            ).toBe(false);
        },
    );


    it(
        'should show an error when loading projects fails',
        () => {
            vi.spyOn(
                console,
                'error',
            ).mockImplementation(
                () => undefined,
            );

            getProjectsUseCaseMock
                .execute
                .mockReturnValue(
                    throwError(
                        () =>
                            new HttpErrorResponse({
                                status: 500,
                            }),
                    ),
                );

            createComponent();

            expect(
                component.error(),
            ).toBe(
                'No se pudieron cargar los proyectos.',
            );

            expect(
                component.loading(),
            ).toBe(false);
        },
    );


    it(
        'should not create a project when the form is invalid',
        () => {
            createComponent();

            component.createProject();

            expect(
                createProjectUseCaseMock.execute,
            ).not.toHaveBeenCalled();

            expect(
                component.projectForm
                    .controls
                    .name
                    .touched,
            ).toBe(true);
        },
    );


    it(
        'should create a project and add it to the beginning of the list',
        () => {
            getProjectsUseCaseMock
                .execute
                .mockReturnValue(
                    of([
                        indexedProject,
                    ]),
                );

            createComponent();

            component.projectForm.setValue({
                name: 'DevPilot',
                description:
                    'Proyecto DevPilot',
            });

            component.createProject();

            expect(
                createProjectUseCaseMock.execute,
            ).toHaveBeenCalledWith({
                name: 'DevPilot',
                description:
                    'Proyecto DevPilot',
            });

            expect(
                component.projects()[0],
            ).toEqual(
                createdProject,
            );

            expect(
                component.projects()[1],
            ).toEqual(
                indexedProject,
            );

            expect(
                component.projectForm
                    .getRawValue(),
            ).toEqual({
                name: '',
                description: '',
            });

            expect(
                component.creating(),
            ).toBe(false);
        },
    );


    it(
        'should expose an error when project creation fails',
        () => {
            vi.spyOn(
                console,
                'error',
            ).mockImplementation(
                () => undefined,
            );

            createProjectUseCaseMock
                .execute
                .mockReturnValue(
                    throwError(
                        () =>
                            new HttpErrorResponse({
                                status: 500,
                            }),
                    ),
                );

            createComponent();

            component.projectForm.setValue({
                name: 'DevPilot',
                description: '',
            });

            component.createProject();

            expect(
                component.error(),
            ).toBe(
                'No se pudo crear el proyecto.',
            );

            expect(
                component.creating(),
            ).toBe(false);
        },
    );


    it(
        'should reject a file that is not a ZIP or RAR',
        () => {
            createComponent();

            const projectId =
                'project-1';

            const file =
                new File(
                    [
                        'content',
                    ],
                    'project.txt',
                    {
                        type:
                            'text/plain',
                    },
                );

            const input =
                document.createElement(
                    'input',
                );

            Object.defineProperty(
                input,
                'files',
                {
                    value: [
                        file,
                    ],
                },
            );

            component.uploadArchive(
                projectId,
                {
                    target:
                        input,
                } as unknown as Event,
            );

            expect(
                component.uploadErrorProjectId(),
            ).toBe(
                projectId,
            );

            expect(
                component.uploadError(),
            ).not.toBeNull();

            expect(
                component.uploadError(),
            ).toContain(
                '.zip',
            );

            expect(
                component.uploadError(),
            ).toContain(
                '.rar',
            );

            expect(
                uploadProjectArchiveUseCaseMock
                    .execute,
            ).not.toHaveBeenCalled();
        },
    );


    it(
        'should upload a ZIP and update the project',
        async () => {
            getProjectsUseCaseMock
                .execute
                .mockReturnValue(
                    of([
                        createdProject,
                        indexedProject,
                    ]),
                );

            createComponent();

            const content =
                new ArrayBuffer(8);

            const file = {
                name:
                    'devpilot.zip',

                type:
                    'application/zip',

                arrayBuffer:
                    vi
                        .fn()
                        .mockResolvedValue(
                            content,
                        ),
            } as unknown as File;

            const input = {
                files: [
                    file,
                ],

                value:
                    'devpilot.zip',
            } as unknown as HTMLInputElement;

            const event = {
                target:
                    input,
            } as unknown as Event;

            component.uploadArchive(
                'project-1',
                event,
            );

            expect(
                component.uploadingProjectId(),
            ).toBe(
                'project-1',
            );

            await vi.waitFor(
                () => {
                    expect(
                        uploadProjectArchiveUseCaseMock
                            .execute,
                    ).toHaveBeenCalledWith(
                        'project-1',
                        {
                            filename:
                                'devpilot.zip',

                            mimeType:
                                'application/zip',

                            content,
                        },
                    );
                },
            );

            await vi.waitFor(
                () => {
                    expect(
                        component.uploadingProjectId(),
                    ).toBeNull();
                },
            );

            expect(
                component.projects()[0],
            ).toEqual(
                indexedUpdatedProject,
            );

            expect(
                input.value,
            ).toBe('');
        },
    );


    it(
        'should return the correct project status labels',
        () => {
            createComponent();

            expect(
                component.getStatusLabel(
                    createdProject,
                ),
            ).toBe(
                'Pendiente',
            );

            expect(
                component.getStatusLabel(
                    indexedProject,
                ),
            ).toBe(
                'Indexado',
            );

            const processingProject = {
                ...createdProject,
                status:
                    'CHUNKED',
            } as Project;

            expect(
                component.getStatusLabel(
                    processingProject,
                ),
            ).toBe(
                'Procesando',
            );

            component
                .uploadingProjectId
                .set(
                    createdProject.id,
                );

            expect(
                component.getStatusLabel(
                    createdProject,
                ),
            ).toBe(
                'Indexando',
            );
        },
    );


    it(
        'should extract the uploaded archive filename',
        () => {
            createComponent();

            expect(
                component.getUploadedFileName(
                    indexedProject,
                ),
            ).toBe(
                'ecommerce.zip',
            );

            expect(
                component.getUploadedFileName(
                    createdProject,
                ),
            ).toBeNull();
        },
    );


    it(
        'should generate a README for an indexed project',
        () => {
            createComponent();

            component.generateReadme(
                indexedProject,
            );

            expect(
                generateReadmeUseCaseMock.execute,
            ).toHaveBeenCalledWith({
                projectId:
                    'project-2',

                language:
                    'es',
            });

            expect(
                component.showReadme(),
            ).toBe(true);

            expect(
                component.readmeProjectName(),
            ).toBe(
                'Angular Ecommerce',
            );

            expect(
                component.generatedReadme(),
            ).toEqual(
                generatedReadme,
            );

            expect(
                component.generatingReadmeProjectId(),
            ).toBeNull();

            expect(
                component.formattedReadme(),
            ).toContain(
                '<h1>DevPilot AI</h1>',
            );
        },
    );


    it(
        'should not generate a README for a project that is not indexed',
        () => {
            createComponent();

            component.generateReadme(
                createdProject,
            );

            expect(
                generateReadmeUseCaseMock.execute,
            ).not.toHaveBeenCalled();

            expect(
                component.showReadme(),
            ).toBe(false);
        },
    );


    it(
        'should show backend detail when README generation fails',
        () => {
            vi.spyOn(
                console,
                'error',
            ).mockImplementation(
                () => undefined,
            );

            generateReadmeUseCaseMock
                .execute
                .mockReturnValue(
                    throwError(
                        () =>
                            new HttpErrorResponse({
                                status:
                                    422,

                                error: {
                                    detail:
                                        'No hay suficiente contexto.',
                                },
                            }),
                    ),
                );

            createComponent();

            component.generateReadme(
                indexedProject,
            );

            expect(
                component.showReadme(),
            ).toBe(false);

            expect(
                component.error(),
            ).toBe(
                'No hay suficiente contexto.',
            );

            expect(
                component.generatingReadmeProjectId(),
            ).toBeNull();
        },
    );


    it(
        'should close and clear the README',
        () => {
            createComponent();

            component.showReadme.set(
                true,
            );

            component.generatedReadme.set(
                generatedReadme,
            );

            component.readmeProjectName.set(
                'Angular Ecommerce',
            );

            component.closeReadme();

            expect(
                component.showReadme(),
            ).toBe(false);

            expect(
                component.generatedReadme(),
            ).toBeNull();

            expect(
                component.readmeProjectName(),
            ).toBeNull();
        },
    );


    it(
        'should open unit tests and load project documents',
        () => {
            createComponent();

            component.openUnitTests(
                indexedProject,
            );

            expect(
                getProjectDocumentsUseCaseMock
                    .execute,
            ).toHaveBeenCalledWith(
                'project-2',
            );

            expect(
                component.showUnitTests(),
            ).toBe(true);

            expect(
                component.selectedUnitTestProjectId(),
            ).toBe(
                'project-2',
            );

            expect(
                component.selectedUnitTestDocumentId(),
            ).toBeNull();

            expect(
                component.unitTestDocuments(),
            ).toEqual(
                projectDocuments,
            );

            expect(
                component.loadingUnitTestDocuments(),
            ).toBe(false);
        },
    );


    it(
        'should not open unit tests for a project that is not indexed',
        () => {
            createComponent();

            component.openUnitTests(
                createdProject,
            );

            expect(
                getProjectDocumentsUseCaseMock
                    .execute,
            ).not.toHaveBeenCalled();

            expect(
                component.showUnitTests(),
            ).toBe(false);
        },
    );


    it(
        'should select a document and clear previously generated tests',
        () => {
            createComponent();

            component.generatedUnitTests.set(
                generatedUnitTests,
            );

            component.selectUnitTestDocument(
                'document-1',
            );

            expect(
                component.selectedUnitTestDocumentId(),
            ).toBe(
                'document-1',
            );

            expect(
                component.generatedUnitTests(),
            ).toBeNull();

            component.selectUnitTestDocument(
                '',
            );

            expect(
                component.selectedUnitTestDocumentId(),
            ).toBeNull();
        },
    );


    it(
        'should not generate unit tests without a selected project and document',
        () => {
            createComponent();

            component.generateUnitTests();

            expect(
                generateUnitTestsUseCaseMock
                    .execute,
            ).not.toHaveBeenCalled();
        },
    );


    it(
        'should generate unit tests for the selected document',
        () => {
            createComponent();

            component.openUnitTests(
                indexedProject,
            );

            component.selectUnitTestDocument(
                'document-1',
            );

            component.generateUnitTests();

            expect(
                generateUnitTestsUseCaseMock
                    .execute,
            ).toHaveBeenCalledWith({
                projectId:
                    'project-2',

                documentId:
                    'document-1',

                framework:
                    null,
            });

            expect(
                component.generatedUnitTests(),
            ).toEqual(
                generatedUnitTests,
            );

            expect(
                component.generatingUnitTests(),
            ).toBe(false);
        },
    );


    it(
        'should show backend detail when unit test generation fails',
        () => {
            vi.spyOn(
                console,
                'error',
            ).mockImplementation(
                () => undefined,
            );

            generateUnitTestsUseCaseMock
                .execute
                .mockReturnValue(
                    throwError(
                        () =>
                            new HttpErrorResponse({
                                status:
                                    422,

                                error: {
                                    detail:
                                        'Archivo no encontrado.',
                                },
                            }),
                    ),
                );

            createComponent();

            component.openUnitTests(
                indexedProject,
            );

            component.selectUnitTestDocument(
                'document-1',
            );

            component.generateUnitTests();

            expect(
                component.error(),
            ).toBe(
                'Archivo no encontrado.',
            );

            expect(
                component.generatingUnitTests(),
            ).toBe(false);
        },
    );


    it(
        'should close and reset the unit test dialog',
        () => {
            createComponent();

            component.showUnitTests.set(
                true,
            );

            component.unitTestDocuments.set(
                projectDocuments,
            );

            component
                .selectedUnitTestProjectId
                .set(
                    'project-2',
                );

            component
                .selectedUnitTestDocumentId
                .set(
                    'document-1',
                );

            component.generatedUnitTests.set(
                generatedUnitTests,
            );

            component.closeUnitTests();

            expect(
                component.showUnitTests(),
            ).toBe(false);

            expect(
                component.unitTestDocuments(),
            ).toEqual([]);

            expect(
                component.selectedUnitTestProjectId(),
            ).toBeNull();

            expect(
                component.selectedUnitTestDocumentId(),
            ).toBeNull();

            expect(
                component.generatedUnitTests(),
            ).toBeNull();
        },
    );


    it(
        'should render generated README information in the template',
        () => {
            createComponent();

            component.showReadme.set(
                true,
            );

            component.readmeProjectName.set(
                'Angular Ecommerce',
            );

            component.generatedReadme.set(
                generatedReadme,
            );

            fixture.detectChanges();

            const compiled =
                fixture.nativeElement as HTMLElement;

            const preview =
                compiled.querySelector(
                    '[data-testid="readme-preview"]',
                );

            expect(
                preview,
            ).not.toBeNull();

            expect(
                preview?.textContent,
            ).toContain(
                'DevPilot AI',
            );

            expect(
                compiled.querySelectorAll(
                    '[data-testid="readme-source"]',
                ),
            ).toHaveLength(
                2,
            );
        },
    );


    it(
        'should render generated unit tests in the template',
        () => {
            createComponent();

            component.showUnitTests.set(
                true,
            );

            component
                .selectedUnitTestProjectId
                .set(
                    'project-2',
                );

            component.unitTestDocuments.set(
                projectDocuments,
            );

            component.generatedUnitTests.set(
                generatedUnitTests,
            );

            fixture.detectChanges();

            const compiled =
                fixture.nativeElement as HTMLElement;

            const code =
                compiled.querySelector(
                    '[data-testid="unit-test-code"]',
                );

            expect(
                code,
            ).not.toBeNull();

            expect(
                code?.textContent,
            ).toContain(
                "describe('App'",
            );

            const resultHeader =
                compiled.querySelector(
                    '[data-testid="unit-test-result-header"]',
                );

            expect(
                resultHeader,
            ).not.toBeNull();

            expect(
                resultHeader?.textContent,
            ).toContain(
                'app.spec.ts',
            );

            const unitTestDialog =
                compiled.querySelector(
                    '[aria-labelledby="unit-test-title"]',
                );

            expect(
                unitTestDialog,
            ).not.toBeNull();

            const sourcesSection =
                unitTestDialog?.querySelector(
                    'aside',
                );

            expect(
                sourcesSection,
            ).not.toBeNull();

            expect(
                sourcesSection?.textContent,
            ).toContain(
                'src/app/app.ts',
            );
        },
    );


    it(
        'should delete a project after confirmation',
        async () => {
            vi.useFakeTimers();

            try {
                createComponent();

                component.projects.set([
                    createdProject,
                    indexedProject,
                ]);

                component.projectToDelete.set(
                    indexedProject,
                );

                await component
                    .confirmProjectDeletion();

                expect(
                    deleteProjectUseCaseMock
                        .execute,
                ).toHaveBeenCalledWith(
                    'project-2',
                );

                expect(
                    component.projects(),
                ).toEqual([
                    createdProject,
                ]);

                expect(
                    component.projectToDelete(),
                ).toBeNull();

                expect(
                    component.deleteProjectSuccess(),
                ).toContain(
                    'Angular Ecommerce',
                );

                expect(
                    component.deletingProjectId(),
                ).toBeNull();
            } finally {
                vi.useRealTimers();
            }
        },
    );


    it(
        'should sanitize malicious HTML from generated README',
        () => {
            createComponent();

            const maliciousReadme:
                GeneratedReadme = {
                content: [
                    '# README seguro',
                    '',
                    '<script>window.__xss = true;</script>',
                    '',
                    '<img src="x" onerror="window.__xss = true">',
                    '',
                    '<p>Contenido legítimo</p>',
                ].join('\n'),

                sources: [],
            };

            component.showReadme.set(
                true,
            );

            component.readmeProjectName.set(
                'Proyecto inseguro',
            );

            component.generatedReadme.set(
                maliciousReadme,
            );

            fixture.detectChanges();

            const compiled =
                fixture.nativeElement as HTMLElement;

            const preview =
                compiled.querySelector(
                    '[data-testid="readme-preview"]',
                );

            expect(
                preview,
            ).not.toBeNull();

            expect(
                preview?.querySelector(
                    'script',
                ),
            ).toBeNull();

            const image =
                preview?.querySelector(
                    'img',
                );

            expect(
                image?.hasAttribute(
                    'onerror',
                ),
            ).toBe(false);

            expect(
                preview?.textContent,
            ).toContain(
                'Contenido legítimo',
            );
        },
    );


    it(
        'should prevent javascript URLs in generated README',
        () => {
            createComponent();

            const maliciousReadme:
                GeneratedReadme = {
                content:
                    '<a href="javascript:alert(\'XSS\')">Enlace malicioso</a>',

                sources: [],
            };

            component.showReadme.set(
                true,
            );

            component.readmeProjectName.set(
                'Proyecto',
            );

            component.generatedReadme.set(
                maliciousReadme,
            );

            fixture.detectChanges();

            const compiled =
                fixture.nativeElement as HTMLElement;

            const link =
                compiled.querySelector(
                    '[data-testid="readme-preview"] a',
                );

            expect(
                link,
            ).not.toBeNull();

            const href =
                link?.getAttribute(
                    'href',
                ) ?? '';

            expect(
                href
                    .toLowerCase()
                    .startsWith(
                        'javascript:',
                    ),
            ).toBe(false);
        },
    );
});