import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import {
    ChatRequest,
    ChatResponse,
} from '@core/domain/chat/chat.model';
import { ChatRepository } from '@core/domain/chat/chat.repository';

@Injectable({
    providedIn: 'root',
})
export class AskProjectQuestionUseCase {
    private readonly chatRepository = inject(ChatRepository);

    execute(
        request: ChatRequest,
    ): Observable<ChatResponse> {
        return this.chatRepository.ask(request);
    }
}