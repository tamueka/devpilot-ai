import {
    ChangeDetectionStrategy,
    Component,
    inject,
} from '@angular/core';
import {
    FormBuilder,
    ReactiveFormsModule,
    Validators,
} from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthStore } from '@core/auth/application/stores/auth.store';


@Component({
    selector: 'app-login',
    standalone: true,
    imports: [
        ReactiveFormsModule,
        RouterLink,
    ],
    templateUrl: './login.html',
    changeDetection:
        ChangeDetectionStrategy.OnPush,
})
export class Login {
    private readonly formBuilder =
        inject(FormBuilder);
    private readonly router =
        inject(Router);
    readonly authStore =
        inject(AuthStore);
    readonly form =
        this.formBuilder.nonNullable.group({
            email: [
                '',
                [
                    Validators.required,
                    Validators.email,
                ],
            ],
            password: [
                '',
                [
                    Validators.required,
                    Validators.minLength(12),
                ],
            ],
        });

    async submit(): Promise<void> {
        this.authStore.clearError();

        if (this.form.invalid) {
            this.form.markAllAsTouched();
            return;
        }
        const success =
            await this.authStore.login(
                this.form.getRawValue(),
            );
        if (!success) {
            return;
        }
        await this.authStore.loadCurrentUser();
        await this.router.navigate([
            '/projects',
        ]);
    }
}