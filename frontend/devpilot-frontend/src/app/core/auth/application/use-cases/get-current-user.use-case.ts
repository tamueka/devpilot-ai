import { inject, Injectable } from '@angular/core';

import { AuthUser } from '../../domain/models/auth.model';
import { AuthRepository } from '../../domain/repositories/auth.repository';

@Injectable({
  providedIn: 'root',
})
export class GetCurrentUserUseCase {
  private readonly authRepository = inject(
    AuthRepository,
  );

  execute(): Promise<AuthUser> {
    return this.authRepository.getCurrentUser();
  }
}