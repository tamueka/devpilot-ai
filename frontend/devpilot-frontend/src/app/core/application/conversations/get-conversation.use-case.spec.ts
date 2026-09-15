import { TestBed } from '@angular/core/testing';
import { firstValueFrom, of } from 'rxjs';
import { vi } from 'vitest';
import { ConversationDetail } from '@core/domain/conversations/conversation.model';
import { ConversationRepository } from '@core/domain/conversations/conversation.repository';
import { GetConversationUseCase } from './get-conversation.use-case';

describe('GetConversationUseCase', () => {
    let useCase: GetConversationUseCase;

    const repositoryMock = {
        getProjectConversations: vi.fn(),
        getConversation: vi.fn(),
    };

    beforeEach(() => {
        repositoryMock.getProjectConversations.mockReset();
        repositoryMock.getConversation.mockReset();

        TestBed.configureTestingModule({
            providers: [
                GetConversationUseCase,
                {
                    provide: ConversationRepository,
                    useValue: repositoryMock,
                },
            ],
        });

        useCase = TestBed.inject(
            GetConversationUseCase,
        );
    });

    it('should get a conversation detail from the repository', async () => {
        const conversation: ConversationDetail = {
            id: 'conversation-1',
            projectId: 'project-123',
            title: '¿Qué hace este archivo?',
            createdAt: '2026-09-08T10:00:00',
            messages: [
                {
                    id: 'message-1',
                    conversationId: 'conversation-1',
                    role: 'user',
                    content: '¿Qué hace este archivo?',
                    sources: null,
                    createdAt: '2026-09-08T10:00:01',
                },
                {
                    id: 'message-2',
                    conversationId: 'conversation-1',
                    role: 'assistant',
                    content: 'Exporta una constante.',
                    sources: [],
                    createdAt: '2026-09-08T10:00:02',
                },
            ],
        };

        repositoryMock.getConversation.mockReturnValue(
            of(conversation),
        );

        const response = await firstValueFrom(
            useCase.execute(
                'conversation-1',
            ),
        );

        expect(
            repositoryMock.getConversation,
        ).toHaveBeenCalledOnce();

        expect(
            repositoryMock.getConversation,
        ).toHaveBeenCalledWith(
            'conversation-1',
        );

        expect(response).toEqual(
            conversation,
        );
    });
});