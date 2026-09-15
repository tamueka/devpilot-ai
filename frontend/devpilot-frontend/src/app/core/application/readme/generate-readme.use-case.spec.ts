import { TestBed } from '@angular/core/testing';
import { firstValueFrom, of } from 'rxjs';
import { vi } from 'vitest';
import {
    GeneratedReadme,
    GenerateReadmeRequest,
} from '@core/domain/readme/readme.model';
import { ReadmeRepository } from '@core/domain/readme/readme.repository';
import { GenerateReadmeUseCase } from './generate-readme.use-case';

describe('GenerateReadmeUseCase', () => {
    let useCase: GenerateReadmeUseCase;

    const repositoryMock = {
        generate: vi.fn(),
    };

    beforeEach(() => {
        repositoryMock.generate.mockReset();

        TestBed.configureTestingModule({
            providers: [
                GenerateReadmeUseCase,
                {
                    provide: ReadmeRepository,
                    useValue: repositoryMock,
                },
            ],
        });

        useCase = TestBed.inject(
            GenerateReadmeUseCase,
        );
    });

    it('should delegate README generation to the repository', async () => {
        const request: GenerateReadmeRequest = {
            projectId: 'project-123',
            language: 'es',
        };

        const expectedResponse: GeneratedReadme = {
            content: '# DevPilot AI',
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