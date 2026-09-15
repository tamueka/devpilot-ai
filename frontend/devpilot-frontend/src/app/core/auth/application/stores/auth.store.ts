import {
    computed,
    inject,
    Injectable,
    signal,
} from '@angular/core';

import {
    AuthUser,
    LoginCredentials,
    RegisterCredentials,
} from '../../domain/models/auth.model';

import { GetCurrentUserUseCase } from '../use-cases/get-current-user.use-case';
import { LoginUseCase } from '../use-cases/login.use-case';
import { RegisterUseCase } from '../use-cases/register.use-case';

import { AuthTokenStorage } from '../../infrastructure/storage/auth-token.storage';


@Injectable({
    providedIn: 'root',
})
export class AuthStore {
    private readonly loginUseCase =
        inject(LoginUseCase);
    private readonly registerUseCase =
        inject(RegisterUseCase);
    private readonly getCurrentUserUseCase =
        inject(GetCurrentUserUseCase);
    private readonly tokenStorage =
        inject(AuthTokenStorage);
    private readonly userSignal =
        signal<AuthUser | null>(
            null,
        );
    private readonly tokenSignal =
        signal<string | null>(
            this.tokenStorage.getToken(),
        );
    private readonly loadingSignal =
        signal(false);
    private readonly errorSignal =
        signal<string | null>(
            null,
        );
    readonly user =
        this.userSignal.asReadonly();
    readonly token =
        this.tokenSignal.asReadonly();
    readonly loading =
        this.loadingSignal.asReadonly();
    readonly error =
        this.errorSignal.asReadonly();
    readonly isAuthenticated =
        computed(
            () =>
                this.tokenSignal() !== null,
        );

    async login(
        credentials: LoginCredentials,
    ): Promise<boolean> {
        this.loadingSignal.set(true);
        this.errorSignal.set(null);

        try {
            const token =
                await this.loginUseCase.execute(
                    credentials,
                );
            this.tokenStorage.setToken(
                token.accessToken,
            );
            this.tokenSignal.set(
                token.accessToken,
            );
            return true;
        } catch {
            this.logout();
            this.errorSignal.set(
                'Email o contraseña incorrectos.',
            );
            return false;
        } finally {
            this.loadingSignal.set(false);
        }
    }

    async register(
        credentials: RegisterCredentials,
    ): Promise<boolean> {
        this.loadingSignal.set(true);
        this.errorSignal.set(null);

        try {
            const user =
                await this.registerUseCase.execute(
                    credentials,
                );

            const token =
                await this.loginUseCase.execute(
                    {
                        email: credentials.email,
                        password:
                            credentials.password,
                    },
                );

            this.tokenStorage.setToken(
                token.accessToken,
            );

            this.tokenSignal.set(
                token.accessToken,
            );

            this.userSignal.set(
                user,
            );

            return true;
        } catch {
            this.logout();

            this.errorSignal.set(
                'No se pudo crear la cuenta.',
            );

            return false;
        } finally {
            this.loadingSignal.set(false);
        }
    }

    async loadCurrentUser(): Promise<void> {
        if (
            !this.tokenSignal()
        ) {
            this.userSignal.set(null);
            return;
        }

        try {
            const user =
                await this.getCurrentUserUseCase.execute();

            this.userSignal.set(
                user,
            );
        } catch {
            this.logout();
        }
    }

    logout(): void {
        this.tokenStorage.clearToken();

        this.tokenSignal.set(null);
        this.userSignal.set(null);
        this.errorSignal.set(null);
    }

    clearError(): void {
        this.errorSignal.set(null);
    }
}
