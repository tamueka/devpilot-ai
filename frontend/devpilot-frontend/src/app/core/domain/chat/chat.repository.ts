import { Observable } from 'rxjs';
import {
    ChatRequest,
    ChatResponse,
} from './chat.model';

export abstract class ChatRepository {
    abstract ask(
        request: ChatRequest,
    ): Observable<ChatResponse>;
}