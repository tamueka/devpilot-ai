import { HttpErrorResponse } from '@angular/common/http';
import {
    Component,
    DestroyRef,
    ElementRef,
    OnInit,
    effect,
    inject,
    signal,
    viewChild,
} from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import {
    FormBuilder,
    ReactiveFormsModule,
    Validators,
} from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { finalize } from 'rxjs';
import { marked } from 'marked';

import { AskProjectQuestionUseCase } from '@core/application/chat/ask-project-question.use-case';
import { GetConversationUseCase } from '@core/application/conversations/get-conversation.use-case';
import { GetProjectConversationsUseCase } from '@core/application/conversations/get-project-conversations.use-case';
import { GetProjectsUseCase } from '@core/application/projects/get-projects.use-case';
import { ChatResponse } from '@core/domain/chat/chat.model';
import {
    Conversation,
    ConversationMessage,
} from '@core/domain/conversations/conversation.model';
import { Project } from '@core/domain/projects/project.model';

@Component({
    selector: 'app-chat',
    standalone: true,
    imports: [ReactiveFormsModule],
    templateUrl: './chat.html',
})
export class Chat implements OnInit {
    private readonly askProjectQuestionUseCase = inject(
        AskProjectQuestionUseCase,
    );

    private readonly getProjectsUseCase = inject(
        GetProjectsUseCase,
    );

    private readonly getProjectConversationsUseCase = inject(
        GetProjectConversationsUseCase,
    );

    private readonly getConversationUseCase = inject(
        GetConversationUseCase,
    );

    private readonly fb = inject(FormBuilder);
    private readonly destroyRef = inject(DestroyRef);
    private readonly route = inject(ActivatedRoute);
    readonly projects = signal<readonly Project[]>([]);
    readonly conversations = signal<readonly Conversation[]>([]);
    readonly messages = signal<readonly ConversationMessage[]>([]);
    private readonly messagesContainer =
        viewChild<ElementRef<HTMLDivElement>>(
            'messagesContainer',
        );
    readonly selectedConversationId = signal<string | null>(null);
    readonly loadingProjects = signal(false);
    readonly loadingConversations = signal(false);
    readonly loadingConversation = signal(false);
    readonly sending = signal(false);

    readonly response = signal<ChatResponse | null>(null);
    readonly error = signal<string | null>(null);

    readonly chatForm = this.fb.nonNullable.group({
        projectId: [
            '',
            [
                Validators.required,
            ],
        ],
        message: [
            '',
            [
                Validators.required,
                Validators.maxLength(4_000),
            ],
        ],
    });

    ngOnInit(): void {
        this.subscribeToProjectChanges();
        this.loadProjects();
    }

    sendMessage(): void {
        if (this.chatForm.invalid) {
            this.chatForm.markAllAsTouched();
            return;
        }

        const formValue = this.chatForm.getRawValue();

        this.sending.set(true);
        this.error.set(null);
        this.response.set(null);

        this.askProjectQuestionUseCase
            .execute({
                projectId: formValue.projectId,
                conversationId: this.selectedConversationId(),
                message: formValue.message,
                topK: 5,
            })
            .pipe(
                finalize(() => {
                    this.sending.set(false);
                }),
                takeUntilDestroyed(this.destroyRef),
            )
            .subscribe({
                next: (response) => {
                    this.response.set(response);

                    this.selectedConversationId.set(
                        response.conversationId,
                    );

                    this.chatForm.controls.message.reset('');

                    this.loadConversation(
                        response.conversationId,
                    );

                    this.loadConversations(
                        formValue.projectId,
                    );
                },
                error: (error: HttpErrorResponse) => {
                    console.error(
                        'Error consultando DevPilot:',
                        error,
                    );

                    this.error.set(
                        this.getErrorMessage(error),
                    );
                },
            });
    }

    selectConversation(
        conversationId: string,
    ): void {
        if (
            this.selectedConversationId() ===
            conversationId
        ) {
            return;
        }

        this.response.set(null);

        this.loadConversation(
            conversationId,
        );
    }

    startNewConversation(): void {
        this.selectedConversationId.set(null);
        this.messages.set([]);
        this.response.set(null);
        this.error.set(null);

        this.chatForm.controls.message.reset('');
    }

    private subscribeToProjectChanges(): void {
        this.chatForm.controls.projectId.valueChanges
            .pipe(
                takeUntilDestroyed(this.destroyRef),
            )
            .subscribe((projectId) => {
                this.selectedConversationId.set(null);
                this.messages.set([]);
                this.response.set(null);
                this.conversations.set([]);
                this.error.set(null);

                if (projectId) {
                    this.loadConversations(projectId);
                }
            });
    }

    private loadProjects(): void {
        this.loadingProjects.set(true);
        this.error.set(null);

        this.getProjectsUseCase
            .execute()
            .pipe(
                finalize(() => {
                    this.loadingProjects.set(false);
                }),
                takeUntilDestroyed(this.destroyRef),
            )
            .subscribe({
                next: (projects) => {
                    const indexedProjects = projects.filter(
                        (project) =>
                            project.status === 'INDEXED',
                    );

                    this.projects.set(indexedProjects);

                    const requestedProjectId =
                        this.route.snapshot.queryParamMap.get(
                            'projectId',
                        );

                    const requestedProjectExists =
                        indexedProjects.some(
                            (project) =>
                                project.id === requestedProjectId,
                        );

                    if (
                        requestedProjectId &&
                        requestedProjectExists
                    ) {
                        this.chatForm.controls.projectId.setValue(
                            requestedProjectId,
                        );
                    }
                },
                error: (error: HttpErrorResponse) => {
                    console.error(
                        'Error cargando proyectos:',
                        error,
                    );

                    this.error.set(
                        'No se pudieron cargar los proyectos.',
                    );
                },
            });
    }

    private loadConversations(
        projectId: string,
    ): void {
        this.loadingConversations.set(true);

        this.getProjectConversationsUseCase
            .execute(projectId)
            .pipe(
                finalize(() => {
                    this.loadingConversations.set(false);
                }),
                takeUntilDestroyed(this.destroyRef),
            )
            .subscribe({
                next: (conversations) => {
                    this.conversations.set(
                        conversations,
                    );
                },
                error: (error: HttpErrorResponse) => {
                    console.error(
                        'Error cargando conversaciones:',
                        error,
                    );

                    this.error.set(
                        'No se pudo cargar el historial de conversaciones.',
                    );
                },
            });
    }

    private loadConversation(
        conversationId: string,
    ): void {
        this.loadingConversation.set(true);
        this.error.set(null);

        this.getConversationUseCase
            .execute(conversationId)
            .pipe(
                finalize(() => {
                    this.loadingConversation.set(false);
                }),
                takeUntilDestroyed(this.destroyRef),
            )
            .subscribe({
                next: (conversation) => {
                    this.selectedConversationId.set(
                        conversation.id,
                    );

                    this.messages.set(
                        conversation.messages,
                    );
                },
                error: (error: HttpErrorResponse) => {
                    console.error(
                        'Error cargando conversación:',
                        error,
                    );

                    this.error.set(
                        'No se pudo cargar la conversación.',
                    );
                },
            });
    }

    formatMarkdown(
        content: string,
    ): string {
        return marked.parse(content, {
            async: false,
        });
    }

    private readonly scrollToLatestMessageEffect =
        effect(() => {
            this.messages();
            this.sending();

            const container =
                this.messagesContainer()?.nativeElement;

            if (!container) {
                return;
            }

            requestAnimationFrame(() => {
                container.scrollTo({
                    top: container.scrollHeight,
                    behavior: 'smooth',
                });
            });
        });

    private getErrorMessage(
        error: HttpErrorResponse,
    ): string {
        if (
            typeof error.error?.detail === 'string'
        ) {
            return error.error.detail;
        }

        return 'No se pudo obtener una respuesta de DevPilot.';
    }
}