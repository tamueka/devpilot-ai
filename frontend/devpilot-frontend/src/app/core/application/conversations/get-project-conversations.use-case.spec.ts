import { TestBed } from '@angular/core/testing';
import { firstValueFrom, of } from 'rxjs';
import { vi } from 'vitest';
import { Conversation } from '@core/domain/conversations/conversation.model';
import { ConversationRepository } from '@core/domain/conversations/conversation.repository';
import { GetProjectConversationsUseCase } from './get-project-conversations.use-case';

describe('GetProjectConversationsUseCase', () => {
    let useCase: GetProjectConversationsUseCase;

    const repositoryMock = {
        getProjectConversations: vi.fn(),
        getConversation: vi.fn(),
    };

    beforeEach(() => {
        repositoryMock.getProjectConversations.mockReset();
        repositoryMock.getConversation.mockReset();

        TestBed.configureTestingModule({
            providers: [
                GetProjectConversationsUseCase,
                {
                    provide: ConversationRepository,
                    useValue: repositoryMock,
                },
            ],
        });

        useCase = TestBed.inject(
            GetProjectConversationsUseCase,
        );
    });

    it('should get project conversations from the repository', async () => {
        const conversations: readonly Conversation[] = [
            {
                id: 'conversation-1',
                projectId: 'project-123',
                title: '¿Qué arquitectura utiliza?',
                createdAt: '2026-09-08T10:00:00',
            },
        ];

        repositoryMock.getProjectConversations.mockReturnValue(
            of(conversations),
        );

        const response = await firstValueFrom(
            useCase.execute(
                'project-123',
            ),
        );

        expect(
            repositoryMock.getProjectConversations,
        ).toHaveBeenCalledOnce();

        expect(
            repositoryMock.getProjectConversations,
        ).toHaveBeenCalledWith(
            'project-123',
        );

        expect(response).toEqual(
            conversations,
        );
    });
});