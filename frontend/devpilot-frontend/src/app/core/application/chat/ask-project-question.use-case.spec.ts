import { TestBed } from '@angular/core/testing';
import { firstValueFrom, of } from 'rxjs';
import { vi } from 'vitest';
import {
    ChatRequest,
    ChatResponse,
} from '@core/domain/chat/chat.model';
import { ChatRepository } from '@core/domain/chat/chat.repository';
import { AskProjectQuestionUseCase } from './ask-project-question.use-case';

describe('AskProjectQuestionUseCase', () => {
    let useCase: AskProjectQuestionUseCase;

    const repositoryMock = {
        ask: vi.fn(),
    };

    beforeEach(() => {
        repositoryMock.ask.mockReset();

        TestBed.configureTestingModule({
            providers: [
                AskProjectQuestionUseCase,
                {
                    provide: ChatRepository,
                    useValue: repositoryMock,
                },
            ],
        });

        useCase = TestBed.inject(
            AskProjectQuestionUseCase,
        );
    });

    it('should delegate the request to ChatRepository', async () => {
        const request: ChatRequest = {
            projectId: 'project-123',
            message: '¿Qué arquitectura utiliza?',
            topK: 5,
        };

        const expectedResponse: ChatResponse = {
            conversationId: 'conversation-123',
            answer: 'El proyecto utiliza una arquitectura modular.',
            sources: [],
        };

        repositoryMock.ask.mockReturnValue(
            of(expectedResponse),
        );

        const response = await firstValueFrom(
            useCase.execute(request),
        );

        expect(
            repositoryMock.ask,
        ).toHaveBeenCalledTimes(1);

        expect(
            repositoryMock.ask,
        ).toHaveBeenCalledWith(
            request,
        );

        expect(response).toEqual(
            expectedResponse,
        );
    });

    it('should preserve conversationId when continuing a conversation', async () => {
        const request: ChatRequest = {
            projectId: 'project-123',
            conversationId: 'conversation-456',
            message: '¿Y dónde se utiliza?',
            topK: 3,
        };

        const expectedResponse: ChatResponse = {
            conversationId: 'conversation-456',
            answer: 'Se utiliza en app.ts.',
            sources: [
                {
                    path: 'src/app/app.ts',
                    language: 'typescript',
                    chunkIndex: 0,
                    excerpt: 'export class App {}',
                },
            ],
        };

        repositoryMock.ask.mockReturnValue(
            of(expectedResponse),
        );

        const response = await firstValueFrom(
            useCase.execute(request),
        );

        expect(
            repositoryMock.ask,
        ).toHaveBeenCalledWith({
            projectId: 'project-123',
            conversationId: 'conversation-456',
            message: '¿Y dónde se utiliza?',
            topK: 3,
        });

        expect(
            response.conversationId,
        ).toBe('conversation-456');

        expect(
            response.sources,
        ).toHaveLength(1);
    });
});