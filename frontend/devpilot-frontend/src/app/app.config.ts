import { provideHttpClient, withInterceptors } from '@angular/common/http';
import {
  ApplicationConfig,
  provideBrowserGlobalErrorListeners,
} from '@angular/core';
import { provideRouter } from '@angular/router';
import { AuthRepository } from '@core/auth/domain/repositories/auth.repository';
import { authErrorInterceptor } from '@core/auth/infrastructure/interceptors/auth-error.interceptor';
import { authInterceptor } from '@core/auth/infrastructure/interceptors/auth.interceptor';
import { HttpAuthRepository } from '@core/auth/infrastructure/repositories/http-auth.repository';
import { ChatRepository } from '@core/domain/chat/chat.repository';
import { ConversationRepository } from '@core/domain/conversations/conversation.repository';
import { ProjectRepository } from '@core/domain/projects/project.repository';
import { ReadmeRepository } from '@core/domain/readme/readme.repository';
import { UnitTestRepository } from '@core/domain/unit-tests/unit-test.repository';
import { ChatApiRepository } from '@core/infrastructure/chat/chat-api.repository';
import { ConversationApiRepository } from '@core/infrastructure/conversations/conversation-api.repository';
import { ProjectApiRepository } from '@core/infrastructure/projects/project-api.repository';
import { ReadmeApiRepository } from '@core/infrastructure/readme/readme-api.repository';
import { UnitTestApiRepository } from '@core/infrastructure/unit-tests/unit-test-api.repository';
import { routes } from './app.routes';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes),
    provideHttpClient(
      withInterceptors([
        authInterceptor,
        authErrorInterceptor,
      ]),
    ),
    {
      provide: ProjectRepository,
      useClass: ProjectApiRepository,
    },
    {
      provide: ChatRepository,
      useClass: ChatApiRepository,
    },
    {
      provide: ConversationRepository,
      useClass: ConversationApiRepository,
    },
    {
      provide: ReadmeRepository,
      useClass: ReadmeApiRepository,
    },
    {
      provide: UnitTestRepository,
      useClass: UnitTestApiRepository,
    },
    {
      provide: AuthRepository,
      useExisting: HttpAuthRepository,
    },
  ],
};