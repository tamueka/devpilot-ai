import { TestBed } from '@angular/core/testing';
import { firstValueFrom, of } from 'rxjs';
import { vi } from 'vitest';
import {
    GeneratedUnitTests,
    GenerateUnitTestsRequest,
} from '@core/domain/unit-tests/unit-test.model';
import { UnitTestRepository } from '@core/domain/unit-tests/unit-test.repository';
import { GenerateUnitTestsUseCase } from './generate-unit-tests.use-case';

describe('GenerateUnitTestsUseCase', () => {
    let useCase: GenerateUnitTestsUseCase;

    const repositoryMock = {
        getProjectDocuments: vi.fn(),
        generate: vi.fn(),
    };

    beforeEach(() => {
        repositoryMock.getProjectDocuments.mockReset();
        repositoryMock.generate.mockReset();

        TestBed.configureTestingModule({
            providers: [
                GenerateUnitTestsUseCase,
                {
                    provide: UnitTestRepository,
                    useValue: repositoryMock,
                },
            ],
        });

        useCase = TestBed.inject(
            GenerateUnitTestsUseCase,
        );
    });

    it('should delegate test generation to the repository', async () => {
        const request: GenerateUnitTestsRequest = {
            projectId: 'project-123',
            documentId: 'document-1',
            framework: 'Vitest',
        };

        const expectedResponse: GeneratedUnitTests = {
            content: 'test("example", () => {});',
            suggestedFilename: 'app.spec.ts',
            sources: [
                {
                    path: 'src/app/app.ts',
                    language: 'typescript',
                },
            ],
        };

        repositoryMock.generate.mockReturnValue(
            of(expectedResponse),
        );

        const response = await firstValueFrom(
            useCase.execute(request),
        );

        expect(
            repositoryMock.generate,
        ).toHaveBeenCalledOnce();

        expect(
            repositoryMock.generate,
        ).toHaveBeenCalledWith(
            request,
        );

        expect(response).toEqual(
            expectedResponse,
        );
    });
});