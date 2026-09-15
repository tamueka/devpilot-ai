import { inject, Injectable } from '@angular/core';

import {
  AuthToken,
  LoginCredentials,
} from '../../domain/models/auth.model';
import { AuthRepository } from '../../domain/repositories/auth.repository';

@Injectable({
  providedIn: 'root',
})
export class LoginUseCase {
  private readonly authRepository = inject(
    AuthRepository,
  );

  execute(
    credentials: LoginCredentials,
  ): Promise<AuthToken> {
    return this.authRepository.login(
      credentials,
    );
  }
}