import { inject, Injectable } from '@angular/core';

import {
  AuthUser,
  RegisterCredentials,
} from '../../domain/models/auth.model';
import { AuthRepository } from '../../domain/repositories/auth.repository';

@Injectable({
  providedIn: 'root',
})
export class RegisterUseCase {
  private readonly authRepository = inject(
    AuthRepository,
  );

  execute(
    credentials: RegisterCredentials,
  ): Promise<AuthUser> {
    return this.authRepository.register(
      credentials,
    );
  }
}
