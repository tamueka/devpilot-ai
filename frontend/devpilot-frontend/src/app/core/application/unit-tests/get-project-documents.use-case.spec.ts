import { TestBed } from '@angular/core/testing';
import { firstValueFrom, of } from 'rxjs';
import { vi } from 'vitest';
import { ProjectDocument } from '@core/domain/unit-tests/unit-test.model';
import { UnitTestRepository } from '@core/domain/unit-tests/unit-test.repository';
import { GetProjectDocumentsUseCase } from './get-project-documents.use-case';

describe('GetProjectDocumentsUseCase', () => {
    let useCase: GetProjectDocumentsUseCase;

    const repositoryMock = {
        getProjectDocuments: vi.fn(),
        generate: vi.fn(),
    };

    beforeEach(() => {
        repositoryMock.getProjectDocuments.mockReset();
        repositoryMock.generate.mockReset();

        TestBed.configureTestingModule({
            providers: [
                GetProjectDocumentsUseCase,
                {
                    provide: UnitTestRepository,
                    useValue: repositoryMock,
                },
            ],
        });

        useCase = TestBed.inject(
            GetProjectDocumentsUseCase,
        );
    });

    it('should get project documents from the repository', async () => {
        const documents: readonly ProjectDocument[] = [
            {
                id: 'document-1',
                projectId: 'project-123',
                path: 'src/app/app.ts',
                filename: 'app.ts',
                extension: '.ts',
                language: 'typescript',
                size: 120,
            },
        ];

        repositoryMock.getProjectDocuments.mockReturnValue(
            of(documents),
        );

        const response = await firstValueFrom(
            useCase.execute(
                'project-123',
            ),
        );

        expect(
            repositoryMock.getProjectDocuments,
        ).toHaveBeenCalledOnce();

        expect(
            repositoryMock.getProjectDocuments,
        ).toHaveBeenCalledWith(
            'project-123',
        );

        expect(response).toEqual(
            documents,
        );
    });
});