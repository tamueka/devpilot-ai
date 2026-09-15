import { HttpErrorResponse } from '@angular/common/http';
import {
    ComponentFixture,
    TestBed,
} from '@angular/core/testing';
import {
    ActivatedRoute,
    convertToParamMap,
} from '@angular/router';
import {
    of,
    Subject,
    throwError,
} from 'rxjs';
import { vi } from 'vitest';
import { AskProjectQuestionUseCase } from '@core/application/chat/ask-project-question.use-case';
import { GetConversationUseCase } from '@core/application/conversations/get-conversation.use-case';
import { GetProjectConversationsUseCase } from '@core/application/conversations/get-project-conversations.use-case';
import { GetProjectsUseCase } from '@core/application/projects/get-projects.use-case';
import { ChatResponse } from '@core/domain/chat/chat.model';
import {
    Conversation,
    ConversationDetail,
    ConversationMessage,
} from '@core/domain/conversations/conversation.model';
import { Project } from '@core/domain/projects/project.model';
import { Chat } from './chat';

describe('Chat', () => {
    let fixture: ComponentFixture<Chat>;
    let component: Chat;

    const askProjectQuestionUseCaseMock = {
        execute: vi.fn(),
    };

    const getProjectsUseCaseMock = {
        execute: vi.fn(),
    };

    const getProjectConversationsUseCaseMock = {
        execute: vi.fn(),
    };

    const getConversationUseCaseMock = {
        execute: vi.fn(),
    };

    const routeMock = {
        snapshot: {
            queryParamMap: convertToParamMap({}),
        },
    };

    const indexedProject = {
        id: 'project-1',
        name: 'DevPilot',
        status: 'INDEXED',
    } as Project;

    const secondIndexedProject = {
        id: 'project-2',
        name: 'Proyecto 2',
        status: 'INDEXED',
    } as Project;

    const createdProject = {
        id: 'project-3',
        name: 'Sin indexar',
        status: 'CREATED',
    } as Project;

    const conversation = {
        id: 'conversation-1',
        projectId: 'project-1',
        title: '¿Qué arquitectura utiliza?',
        createdAt: '2026-09-08T10:00:00',
    } as Conversation;

    const userMessage = {
        id: 'message-1',
        conversationId: 'conversation-1',
        role: 'user',
        content: '¿Qué hace este proyecto?',
        sources: null,
        createdAt: '2026-09-08T10:00:01',
    } as ConversationMessage;

    const assistantMessage = {
        id: 'message-2',
        conversationId: 'conversation-1',
        role: 'assistant',
        content: 'El proyecto utiliza Angular.',
        sources: [
            {
                path: 'src/app/app.ts',
                language: 'typescript',
                chunkIndex: 2,
                excerpt: 'export class App {}',
            },
        ],
        createdAt: '2026-09-08T10:00:02',
    } as ConversationMessage;

    const conversationDetail = {
        id: 'conversation-1',
        projectId: 'project-1',
        title: '¿Qué arquitectura utiliza?',
        createdAt: '2026-09-08T10:00:00',
        messages: [
            userMessage,
            assistantMessage,
        ],
    } as ConversationDetail;

    const chatResponse: ChatResponse = {
        conversationId: 'conversation-1',
        answer: 'El proyecto utiliza Angular.',
        sources: [
            {
                path: 'src/app/app.ts',
                language: 'typescript',
                chunkIndex: 2,
                excerpt: 'export class App {}',
            },
        ],
    };

    beforeEach(async () => {
        vi.stubGlobal(
            'requestAnimationFrame',
            vi.fn(() => 1),
        );

        askProjectQuestionUseCaseMock.execute.mockReset();

        getProjectsUseCaseMock.execute.mockReset();

        getProjectConversationsUseCaseMock.execute.mockReset();

        getConversationUseCaseMock.execute.mockReset();

        routeMock.snapshot.queryParamMap =
            convertToParamMap({});

        getProjectsUseCaseMock.execute.mockReturnValue(
            of([]),
        );

        getProjectConversationsUseCaseMock.execute.mockReturnValue(
            of([]),
        );

        getConversationUseCaseMock.execute.mockReturnValue(
            of(conversationDetail),
        );

        askProjectQuestionUseCaseMock.execute.mockReturnValue(
            of(chatResponse),
        );

        await TestBed.configureTestingModule({
            imports: [
                Chat,
            ],
            providers: [
                {
                    provide: AskProjectQuestionUseCase,
                    useValue:
                        askProjectQuestionUseCaseMock,
                },
                {
                    provide: GetProjectsUseCase,
                    useValue:
                        getProjectsUseCaseMock,
                },
                {
                    provide:
                        GetProjectConversationsUseCase,
                    useValue:
                        getProjectConversationsUseCaseMock,
                },
                {
                    provide: GetConversationUseCase,
                    useValue:
                        getConversationUseCaseMock,
                },
                {
                    provide: ActivatedRoute,
                    useValue: routeMock,
                },
            ],
        }).compileComponents();
    });

    afterEach(() => {
        vi.unstubAllGlobals();
    });

    function createComponent(): void {
        fixture =
            TestBed.createComponent(Chat);

        component =
            fixture.componentInstance;

        fixture.detectChanges();
    }

    it('should create the component and load only indexed projects', () => {
        getProjectsUseCaseMock.execute.mockReturnValue(
            of([
                indexedProject,
                createdProject,
                secondIndexedProject,
            ]),
        );

        createComponent();

        expect(component).toBeTruthy();

        expect(
            getProjectsUseCaseMock.execute,
        ).toHaveBeenCalledOnce();

        expect(
            component.projects(),
        ).toEqual([
            indexedProject,
            secondIndexedProject,
        ]);

        expect(
            component.loadingProjects(),
        ).toBe(false);
    });

    it('should select the project received through the query parameter', () => {
        routeMock.snapshot.queryParamMap =
            convertToParamMap({
                projectId: 'project-1',
            });

        getProjectsUseCaseMock.execute.mockReturnValue(
            of([
                indexedProject,
            ]),
        );

        getProjectConversationsUseCaseMock.execute.mockReturnValue(
            of([
                conversation,
            ]),
        );

        createComponent();

        expect(
            component.chatForm.controls.projectId.value,
        ).toBe('project-1');

        expect(
            getProjectConversationsUseCaseMock.execute,
        ).toHaveBeenCalledWith(
            'project-1',
        );

        expect(
            component.conversations(),
        ).toEqual([
            conversation,
        ]);
    });

    it('should not send an invalid form', () => {
        createComponent();

        component.sendMessage();

        expect(
            askProjectQuestionUseCaseMock.execute,
        ).not.toHaveBeenCalled();

        expect(
            component.chatForm.controls.projectId.touched,
        ).toBe(true);

        expect(
            component.chatForm.controls.message.touched,
        ).toBe(true);
    });

    it('should send a new question without a conversation id', () => {
        getProjectConversationsUseCaseMock.execute.mockReturnValue(
            of([
                conversation,
            ]),
        );

        getConversationUseCaseMock.execute.mockReturnValue(
            of(conversationDetail),
        );

        createComponent();

        component.chatForm.controls.projectId.setValue(
            'project-1',
        );

        component.chatForm.controls.message.setValue(
            '¿Qué arquitectura utiliza?',
        );

        component.sendMessage();

        expect(
            askProjectQuestionUseCaseMock.execute,
        ).toHaveBeenCalledWith({
            projectId: 'project-1',
            conversationId: null,
            message: '¿Qué arquitectura utiliza?',
            topK: 5,
        });

        expect(
            component.selectedConversationId(),
        ).toBe('conversation-1');

        expect(
            component.messages(),
        ).toEqual(
            conversationDetail.messages,
        );

        expect(
            component.response(),
        ).toEqual(chatResponse);

        expect(
            component.chatForm.controls.message.value,
        ).toBe('');

        expect(
            component.sending(),
        ).toBe(false);
    });

    it('should send the current conversation id when continuing a conversation', () => {
        createComponent();

        component.chatForm.controls.projectId.setValue(
            'project-1',
        );

        component.selectedConversationId.set(
            'conversation-1',
        );

        component.chatForm.controls.message.setValue(
            '¿Y dónde se utiliza?',
        );

        component.sendMessage();

        expect(
            askProjectQuestionUseCaseMock.execute,
        ).toHaveBeenCalledWith({
            projectId: 'project-1',
            conversationId: 'conversation-1',
            message: '¿Y dónde se utiliza?',
            topK: 5,
        });
    });

    it('should keep sending state active while the request is pending', () => {
        const responseSubject =
            new Subject<ChatResponse>();

        askProjectQuestionUseCaseMock.execute.mockReturnValue(
            responseSubject.asObservable(),
        );

        createComponent();

        component.chatForm.controls.projectId.setValue(
            'project-1',
        );

        component.chatForm.controls.message.setValue(
            '¿Qué hace?',
        );

        component.sendMessage();

        expect(
            component.sending(),
        ).toBe(true);

        responseSubject.complete();

        expect(
            component.sending(),
        ).toBe(false);
    });

    it('should not reload the currently selected conversation', () => {
        createComponent();

        component.selectedConversationId.set(
            'conversation-1',
        );

        getConversationUseCaseMock.execute.mockClear();

        component.selectConversation(
            'conversation-1',
        );

        expect(
            getConversationUseCaseMock.execute,
        ).not.toHaveBeenCalled();
    });

    it('should load another conversation when selected', () => {
        getConversationUseCaseMock.execute.mockReturnValue(
            of(conversationDetail),
        );

        createComponent();

        component.selectConversation(
            'conversation-1',
        );

        expect(
            getConversationUseCaseMock.execute,
        ).toHaveBeenCalledWith(
            'conversation-1',
        );

        expect(
            component.selectedConversationId(),
        ).toBe('conversation-1');

        expect(
            component.messages(),
        ).toEqual(
            conversationDetail.messages,
        );

        expect(
            component.loadingConversation(),
        ).toBe(false);
    });

    it('should reset state when starting a new conversation', () => {
        createComponent();

        component.selectedConversationId.set(
            'conversation-1',
        );

        component.messages.set([
            userMessage,
            assistantMessage,
        ]);

        component.response.set(
            chatResponse,
        );

        component.error.set(
            'Error anterior',
        );

        component.chatForm.controls.message.setValue(
            'Mensaje anterior',
        );

        component.startNewConversation();

        expect(
            component.selectedConversationId(),
        ).toBeNull();

        expect(
            component.messages(),
        ).toEqual([]);

        expect(
            component.response(),
        ).toBeNull();

        expect(
            component.error(),
        ).toBeNull();

        expect(
            component.chatForm.controls.message.value,
        ).toBe('');
    });

    it('should expose the backend error detail when sending fails', () => {
        vi.spyOn(
            console,
            'error',
        ).mockImplementation(
            () => undefined,
        );

        askProjectQuestionUseCaseMock.execute.mockReturnValue(
            throwError(
                () =>
                    new HttpErrorResponse({
                        status: 500,
                        error: {
                            detail:
                                'Error controlado desde FastAPI.',
                        },
                    }),
            ),
        );

        createComponent();

        component.chatForm.controls.projectId.setValue(
            'project-1',
        );

        component.chatForm.controls.message.setValue(
            '¿Qué hace?',
        );

        component.sendMessage();

        expect(
            component.error(),
        ).toBe(
            'Error controlado desde FastAPI.',
        );

        expect(
            component.sending(),
        ).toBe(false);
    });

    it('should render assistant sources in the template', () => {
        createComponent();

        component.messages.set([
            userMessage,
            assistantMessage,
        ]);

        fixture.detectChanges();

        const compiled =
            fixture.nativeElement as HTMLElement;

        const sourceCard =
            fixture.nativeElement.querySelector(
                '[data-testid="source-card"]',
            ) as HTMLElement | null;

        expect(
            sourceCard,
        ).not.toBeNull();

        expect(
            sourceCard?.textContent,
        ).toContain(
            'src/app/app.ts',
        );

        expect(
            sourceCard?.textContent,
        ).toContain(
            'typescript',
        );

        expect(
            sourceCard?.textContent,
        ).toContain(
            'Chunk 2',
        );

        expect(
            sourceCard?.textContent,
        ).toContain(
            'export class App {}',
        );
    });

    it('should sanitize malicious HTML from assistant messages', () => {
        createComponent();

        const maliciousMessage = {
            id: 'message-xss',
            conversationId: 'conversation-1',
            role: 'assistant',
            content: [
                '<script>window.__xss = true;</script>',
                '<img src="x" onerror="window.__xss = true">',
                '<p>Contenido válido</p>',
            ].join(''),
            sources: [],
            createdAt: '2026-09-08T10:00:00',
        } as ConversationMessage;

        component.messages.set([
            maliciousMessage,
        ]);

        fixture.detectChanges();

        const compiled =
            fixture.nativeElement as HTMLElement;

        const markdown =
            compiled.querySelector(
                '[data-testid="assistant-markdown"]',
            );

        expect(markdown).not.toBeNull();

        expect(
            markdown?.querySelector(
                'script',
            ),
        ).toBeNull();

        const image =
            markdown?.querySelector(
                'img',
            );

        expect(
            image?.hasAttribute(
                'onerror',
            ),
        ).toBe(false);

        expect(
            markdown?.textContent,
        ).toContain(
            'Contenido válido',
        );
    });

    it('should prevent javascript URLs in assistant content', () => {
        createComponent();

        const maliciousMessage = {
            id: 'message-link',
            conversationId: 'conversation-1',
            role: 'assistant',
            content:
                '<a href="javascript:alert(\'XSS\')">Enlace malicioso</a>',
            sources: [],
            createdAt: '2026-09-08T10:00:00',
        } as ConversationMessage;

        component.messages.set([
            maliciousMessage,
        ]);

        fixture.detectChanges();

        const compiled =
            fixture.nativeElement as HTMLElement;

        const link =
            compiled.querySelector(
                '[data-testid="assistant-markdown"] a',
            );

        expect(link).not.toBeNull();

        const href =
            link?.getAttribute(
                'href',
            ) ?? '';

        expect(
            href
                .toLowerCase()
                .startsWith(
                    'javascript:',
                ),
        ).toBe(false);
    });

    it('should sanitize malicious HTML from assistant messages', () => {
        createComponent();

        const maliciousMessage = {
            id: 'message-xss',
            conversationId: 'conversation-1',
            role: 'assistant',
            content: [
                '<script>window.__xss = true;</script>',
                '<img src="x" onerror="window.__xss = true">',
                '<p>Contenido válido</p>',
            ].join(''),
            sources: [],
            createdAt: '2026-09-08T10:00:00',
        } as ConversationMessage;

        component.messages.set([
            maliciousMessage,
        ]);

        fixture.detectChanges();

        const compiled =
            fixture.nativeElement as HTMLElement;

        const markdown =
            compiled.querySelector(
                '[data-testid="assistant-markdown"]',
            );

        expect(markdown).not.toBeNull();

        expect(
            markdown?.querySelector(
                'script',
            ),
        ).toBeNull();

        const image =
            markdown?.querySelector(
                'img',
            );

        expect(
            image?.hasAttribute(
                'onerror',
            ),
        ).toBe(false);

        expect(
            markdown?.textContent,
        ).toContain(
            'Contenido válido',
        );
    });

    it('should prevent javascript URLs in assistant content', () => {
        createComponent();

        const maliciousMessage = {
            id: 'message-link',
            conversationId: 'conversation-1',
            role: 'assistant',
            content:
                '<a href="javascript:alert(\'XSS\')">Enlace malicioso</a>',
            sources: [],
            createdAt: '2026-09-08T10:00:00',
        } as ConversationMessage;

        component.messages.set([
            maliciousMessage,
        ]);

        fixture.detectChanges();

        const compiled =
            fixture.nativeElement as HTMLElement;

        const link =
            compiled.querySelector(
                '[data-testid="assistant-markdown"] a',
            );

        expect(link).not.toBeNull();

        const href =
            link?.getAttribute(
                'href',
            ) ?? '';

        expect(
            href
                .toLowerCase()
                .startsWith(
                    'javascript:',
                ),
        ).toBe(false);
    });
});