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

import {
    ChatApiRepository,
} from './chat-api.repository';

import {
    environment,
} from '@env/environment';


describe('ChatApiRepository', () => {
    let repository: ChatApiRepository;
    let httpTestingController: HttpTestingController;

    beforeEach(() => {
        TestBed.configureTestingModule({
            providers: [
                provideHttpClient(),
                provideHttpClientTesting(),
                ChatApiRepository,
            ],
        });

        repository = TestBed.inject(
            ChatApiRepository,
        );

        httpTestingController = TestBed.inject(
            HttpTestingController,
        );
    });

    afterEach(() => {
        httpTestingController.verify();
    });

    it('should send a new conversation request', async () => {
        const responsePromise = firstValueFrom(
            repository.ask({
                projectId: 'project-123',
                message: '¿Qué hace este proyecto?',
                topK: 5,
            }),
        );

        const request =
            httpTestingController.expectOne(
                `${environment.apiUrl}/chat`,
            );

        expect(
            request.request.method,
        ).toBe('POST');

        expect(
            request.request.body,
        ).toEqual({
            project_id: 'project-123',
            message: '¿Qué hace este proyecto?',
            top_k: 5,
        });

        request.flush({
            conversation_id:
                'conversation-123',

            answer:
                'El proyecto utiliza Angular.',

            sources: [
                {
                    path: 'src/app/app.ts',
                    language: 'typescript',
                    chunk_index: 2,
                    excerpt:
                        'export class App {}',
                },
            ],
        });

        const response =
            await responsePromise;

        expect(response).toEqual({
            conversationId:
                'conversation-123',

            answer:
                'El proyecto utiliza Angular.',

            sources: [
                {
                    path: 'src/app/app.ts',
                    language: 'typescript',
                    chunkIndex: 2,
                    excerpt:
                        'export class App {}',
                },
            ],
        });
    });

    it('should send conversationId when continuing a conversation', async () => {
        const responsePromise = firstValueFrom(
            repository.ask({
                projectId: 'project-123',
                conversationId:
                    'conversation-456',
                message:
                    '¿Y dónde se utiliza?',
                topK: 3,
            }),
        );

        const request =
            httpTestingController.expectOne(
                `${environment.apiUrl}/chat`,
            );

        expect(
            request.request.body,
        ).toEqual({
            project_id: 'project-123',
            conversation_id:
                'conversation-456',
            message:
                '¿Y dónde se utiliza?',
            top_k: 3,
        });

        request.flush({
            conversation_id:
                'conversation-456',
            answer:
                'Se utiliza en app.ts.',
            sources: [],
        });

        const response =
            await responsePromise;

        expect(
            response.conversationId,
        ).toBe(
            'conversation-456',
        );

        expect(
            response.answer,
        ).toBe(
            'Se utiliza en app.ts.',
        );
    });

    it('should omit top_k when it is not provided', async () => {
        const responsePromise = firstValueFrom(
            repository.ask({
                projectId: 'project-123',
                message:
                    'Explica la arquitectura.',
            }),
        );

        const request =
            httpTestingController.expectOne(
                `${environment.apiUrl}/chat`,
            );

        expect(
            request.request.body,
        ).toEqual({
            project_id: 'project-123',
            message:
                'Explica la arquitectura.',
        });

        request.flush({
            conversation_id:
                'conversation-789',
            answer:
                'Respuesta.',
            sources: [],
        });

        await responsePromise;
    });

    it('should map multiple sources to the domain model', async () => {
        const responsePromise = firstValueFrom(
            repository.ask({
                projectId: 'project-123',
                message:
                    '¿Qué archivos son relevantes?',
            }),
        );

        const request =
            httpTestingController.expectOne(
                `${environment.apiUrl}/chat`,
            );

        request.flush({
            conversation_id:
                'conversation-123',

            answer:
                'Hay dos archivos relevantes.',

            sources: [
                {
                    path:
                        'src/app/app.ts',
                    language:
                        'typescript',
                    chunk_index: 0,
                    excerpt:
                        'export class App {}',
                },
                {
                    path:
                        'src/app/app.config.ts',
                    language:
                        'typescript',
                    chunk_index: 3,
                    excerpt:
                        'export const appConfig = {};',
                },
            ],
        });

        const response =
            await responsePromise;

        expect(
            response.sources,
        ).toHaveLength(2);

        expect(
            response.sources[0],
        ).toEqual({
            path:
                'src/app/app.ts',
            language:
                'typescript',
            chunkIndex: 0,
            excerpt:
                'export class App {}',
        });

        expect(
            response.sources[1],
        ).toEqual({
            path:
                'src/app/app.config.ts',
            language:
                'typescript',
            chunkIndex: 3,
            excerpt:
                'export const appConfig = {};',
        });
    });
});