import {
    provideHttpClient,
} from '@angular/common/http';
import {
    HttpTestingController,
    provideHttpClientTesting,
} from '@angular/common/http/testing';
import {
    TestBed,
} from '@angular/core/testing';
import { environment } from '@env/environment';
import {
    firstValueFrom,
} from 'rxjs';
import {
    ReadmeApiRepository,
} from './readme-api.repository';

describe('ReadmeApiRepository', () => {
    let repository: ReadmeApiRepository;
    let httpTestingController: HttpTestingController;

    beforeEach(() => {
        TestBed.configureTestingModule({
            providers: [
                provideHttpClient(),
                provideHttpClientTesting(),
                ReadmeApiRepository,
            ],
        });

        repository = TestBed.inject(
            ReadmeApiRepository,
        );

        httpTestingController = TestBed.inject(
            HttpTestingController,
        );
    });

    afterEach(() => {
        httpTestingController.verify();
    });

    it('should generate a README and map the response', async () => {
        const responsePromise = firstValueFrom(
            repository.generate({
                projectId: 'project-123',
                language: 'es',
            }),
        );

        const request =
            httpTestingController.expectOne(
                `${environment.apiUrl}/projects/project-123/readme`,
            );

        expect(
            request.request.method,
        ).toBe('POST');

        expect(
            request.request.body,
        ).toEqual({
            project_id: 'project-123',
            language: 'es',
        });

        request.flush({
            content:
                '# DevPilot AI\n\nREADME generado.',

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
        });

        const response =
            await responsePromise;

        expect(response).toEqual({
            content:
                '# DevPilot AI\n\nREADME generado.',

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
        });
    });

    it('should support English README generation', async () => {
        const responsePromise = firstValueFrom(
            repository.generate({
                projectId: 'project-456',
                language: 'en',
            }),
        );

        const request =
            httpTestingController.expectOne(
                `${environment.apiUrl}/projects/project-456/readme`,
            );

        expect(
            request.request.body,
        ).toEqual({
            project_id: 'project-456',
            language: 'en',
        });

        request.flush({
            content: '# Project',
            sources: [],
        });

        const response =
            await responsePromise;

        expect(
            response.content,
        ).toBe('# Project');

        expect(
            response.sources,
        ).toEqual([]);
    });
});