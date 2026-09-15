import {
    inject,
    Injectable,
} from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

import {
    AuthToken,
    AuthUser,
    LoginCredentials,
    RegisterCredentials,
} from '../../domain/models/auth.model';
import { AuthRepository } from '../../domain/repositories/auth.repository';

import { environment } from '@env/environment';


interface TokenResponseDto {
    access_token: string;
    token_type: string;
}

interface UserResponseDto {
    id: string;
    email: string;
    is_active: boolean;
    created_at: string;
}


@Injectable({
    providedIn: 'root',
})
export class HttpAuthRepository
    extends AuthRepository {
    private readonly http = inject(
        HttpClient,
    );

    private readonly apiUrl =
        environment.apiUrl;

    async login(
        credentials: LoginCredentials,
    ): Promise<AuthToken> {
        const response = await firstValueFrom(
            this.http.post<TokenResponseDto>(
                `${this.apiUrl}/auth/login`,
                {
                    email: credentials.email,
                    password: credentials.password,
                },
            ),
        );

        return {
            accessToken:
                response.access_token,
            tokenType:
                response.token_type,
        };
    }

    async register(
        credentials: RegisterCredentials,
    ): Promise<AuthUser> {
        const response = await firstValueFrom(
            this.http.post<UserResponseDto>(
                `${this.apiUrl}/auth/register`,
                {
                    email: credentials.email,
                    password: credentials.password,
                },
            ),
        );

        return this.mapUser(
            response,
        );
    }

    async getCurrentUser(): Promise<AuthUser> {
        const response = await firstValueFrom(
            this.http.get<UserResponseDto>(
                `${this.apiUrl}/auth/me`,
            ),
        );

        return this.mapUser(
            response,
        );
    }

    private mapUser(
        user: UserResponseDto,
    ): AuthUser {
        return {
            id: user.id,
            email: user.email,
            isActive: user.is_active,
            createdAt: user.created_at,
        };
    }
}