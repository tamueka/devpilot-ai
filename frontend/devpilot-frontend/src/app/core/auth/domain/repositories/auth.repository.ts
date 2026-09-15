import {
  AuthToken,
  AuthUser,
  LoginCredentials,
  RegisterCredentials,
} from '../models/auth.model';

export abstract class AuthRepository {
  abstract login(
    credentials: LoginCredentials,
  ): Promise<AuthToken>;

  abstract register(
    credentials: RegisterCredentials,
  ): Promise<AuthUser>;

  abstract getCurrentUser(): Promise<AuthUser>;
}