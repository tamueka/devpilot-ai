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
    ConversationApiRepository,
} from './conversation-api.repository';

describe('ConversationApiRepository', () => {
    let repository: ConversationApiRepository;
    let httpTestingController: HttpTestingController;

    beforeEach(() => {
        TestBed.configureTestingModule({
            providers: [
                provideHttpClient(),
                provideHttpClientTesting(),
                ConversationApiRepository,
            ],
        });

        repository = TestBed.inject(
            ConversationApiRepository,
        );

        httpTestingController = TestBed.inject(
            HttpTestingController,
        );
    });

    afterEach(() => {
        httpTestingController.verify();
    });

    it('should get project conversations and map them', async () => {
        const responsePromise = firstValueFrom(
            repository.getProjectConversations(
                'project-123',
            ),
        );

        const request =
            httpTestingController.expectOne(
                `${environment.apiUrl}/projects/project-123/conversations`,
            );

        expect(
            request.request.method,
        ).toBe('GET');

        request.flush([
            {
                id: 'conversation-1',
                project_id: 'project-123',
                title: '¿Qué hace este proyecto?',
                created_at:
                    '2026-09-08T10:00:00',
            },
            {
                id: 'conversation-2',
                project_id: 'project-123',
                title: null,
                created_at:
                    '2026-09-08T11:00:00',
            },
        ]);

        const conversations =
            await responsePromise;

        expect(conversations).toEqual([
            {
                id: 'conversation-1',
                projectId: 'project-123',
                title:
                    '¿Qué hace este proyecto?',
                createdAt:
                    '2026-09-08T10:00:00',
            },
            {
                id: 'conversation-2',
                projectId: 'project-123',
                title: null,
                createdAt:
                    '2026-09-08T11:00:00',
            },
        ]);
    });

    it('should get conversation detail and map messages', async () => {
        const responsePromise = firstValueFrom(
            repository.getConversation(
                'conversation-1',
            ),
        );

        const request =
            httpTestingController.expectOne(
                `${environment.apiUrl}/conversations/conversation-1`,
            );

        expect(
            request.request.method,
        ).toBe('GET');

        request.flush({
            id: 'conversation-1',
            project_id: 'project-123',
            title:
                '¿Qué hace este archivo?',
            created_at:
                '2026-09-08T10:00:00',

            messages: [
                {
                    id: 'message-1',
                    conversation_id:
                        'conversation-1',
                    role: 'user',
                    content:
                        '¿Qué hace este archivo?',
                    sources: null,
                    created_at:
                        '2026-09-08T10:00:01',
                },
                {
                    id: 'message-2',
                    conversation_id:
                        'conversation-1',
                    role: 'assistant',
                    content:
                        'Exporta una constante.',
                    sources: [
                        {
                            path:
                                'src/app/app.ts',
                            language:
                                'typescript',
                            chunk_index: 2,
                            excerpt:
                                "export const hello = 'DevPilot AI';",
                        },
                    ],
                    created_at:
                        '2026-09-08T10:00:02',
                },
            ],
        });

        const conversation =
            await responsePromise;

        expect(conversation).toEqual({
            id: 'conversation-1',
            projectId: 'project-123',
            title:
                '¿Qué hace este archivo?',
            createdAt:
                '2026-09-08T10:00:00',

            messages: [
                {
                    id: 'message-1',
                    conversationId:
                        'conversation-1',
                    role: 'user',
                    content:
                        '¿Qué hace este archivo?',
                    sources: null,
                    createdAt:
                        '2026-09-08T10:00:01',
                },
                {
                    id: 'message-2',
                    conversationId:
                        'conversation-1',
                    role: 'assistant',
                    content:
                        'Exporta una constante.',
                    sources: [
                        {
                            path:
                                'src/app/app.ts',
                            language:
                                'typescript',
                            chunkIndex: 2,
                            excerpt:
                                "export const hello = 'DevPilot AI';",
                        },
                    ],
                    createdAt:
                        '2026-09-08T10:00:02',
                },
            ],
        });
    });
});