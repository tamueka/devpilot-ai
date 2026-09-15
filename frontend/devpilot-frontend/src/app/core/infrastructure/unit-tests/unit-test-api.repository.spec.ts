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
import {
    firstValueFrom,
} from 'rxjs';
import { environment } from '@env/environment';
import {
    UnitTestApiRepository,
} from './unit-test-api.repository';

describe('UnitTestApiRepository', () => {
    let repository: UnitTestApiRepository;
    let httpTestingController: HttpTestingController;

    beforeEach(() => {
        TestBed.configureTestingModule({
            providers: [
                provideHttpClient(),
                provideHttpClientTesting(),
                UnitTestApiRepository,
            ],
        });

        repository = TestBed.inject(
            UnitTestApiRepository,
        );

        httpTestingController = TestBed.inject(
            HttpTestingController,
        );
    });

    afterEach(() => {
        httpTestingController.verify();
    });

    it('should get project documents and map them to the domain', async () => {
        const responsePromise = firstValueFrom(
            repository.getProjectDocuments(
                'project-123',
            ),
        );

        const request =
            httpTestingController.expectOne(
                `${environment.apiUrl}/projects/project-123/documents`,
            );

        expect(
            request.request.method,
        ).toBe('GET');

        request.flush([
            {
                id: 'document-1',
                project_id: 'project-123',
                path: 'src/app/app.ts',
                filename: 'app.ts',
                extension: '.ts',
                language: 'typescript',
                size: 120,
            },
            {
                id: 'document-2',
                project_id: 'project-123',
                path: 'package.json',
                filename: 'package.json',
                extension: '.json',
                language: 'json',
                size: 500,
            },
        ]);

        const documents =
            await responsePromise;

        expect(documents).toEqual([
            {
                id: 'document-1',
                projectId: 'project-123',
                path: 'src/app/app.ts',
                filename: 'app.ts',
                extension: '.ts',
                language: 'typescript',
                size: 120,
            },
            {
                id: 'document-2',
                projectId: 'project-123',
                path: 'package.json',
                filename: 'package.json',
                extension: '.json',
                language: 'json',
                size: 500,
            },
        ]);
    });

    it('should generate unit tests and map the response', async () => {
        const responsePromise = firstValueFrom(
            repository.generate({
                projectId: 'project-123',
                documentId: 'document-1',
                framework: null,
            }),
        );

        const request =
            httpTestingController.expectOne(
                `${environment.apiUrl}/projects/project-123/unit-tests`,
            );

        expect(
            request.request.method,
        ).toBe('POST');

        expect(
            request.request.body,
        ).toEqual({
            project_id: 'project-123',
            document_id: 'document-1',
            framework: null,
        });

        request.flush({
            content:
                "describe('App', () => {});",

            suggested_filename:
                'app.spec.ts',

            sources: [
                {
                    path: 'src/app/app.ts',
                    language: 'typescript',
                },
            ],
        });

        const response =
            await responsePromise;

        expect(response).toEqual({
            content:
                "describe('App', () => {});",

            suggestedFilename:
                'app.spec.ts',

            sources: [
                {
                    path: 'src/app/app.ts',
                    language: 'typescript',
                },
            ],
        });
    });

    it('should send an explicit testing framework', async () => {
        const responsePromise = firstValueFrom(
            repository.generate({
                projectId: 'project-123',
                documentId: 'document-1',
                framework: 'Vitest',
            }),
        );

        const request =
            httpTestingController.expectOne(
                `${environment.apiUrl}/projects/project-123/unit-tests`,
            );

        expect(
            request.request.body,
        ).toEqual({
            project_id: 'project-123',
            document_id: 'document-1',
            framework: 'Vitest',
        });

        request.flush({
            content: 'test("example", () => {});',
            suggested_filename:
                'app.spec.ts',
            sources: [],
        });

        await responsePromise;
    });
});