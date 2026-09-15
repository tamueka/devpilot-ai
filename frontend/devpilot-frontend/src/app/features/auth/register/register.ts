import {
    ChangeDetectionStrategy,
    Component,
    inject,
} from '@angular/core';
import {
    AbstractControl,
    FormBuilder,
    ReactiveFormsModule,
    ValidationErrors,
    ValidatorFn,
    Validators,
} from '@angular/forms';
import {
    Router,
    RouterLink,
} from '@angular/router';
import { AuthStore } from '@core/auth/application/stores/auth.store';


const passwordsMatchValidator: ValidatorFn = (
    control: AbstractControl,
): ValidationErrors | null => {
    const password =
        control.get('password')?.value;
    const confirmPassword =
        control.get('confirmPassword')?.value;
    if (
        !password
        || !confirmPassword
    ) {
        return null;
    }
    return password === confirmPassword
        ? null
        : {
            passwordsMismatch: true,
        };
};


@Component({
    selector: 'app-register',
    standalone: true,
    imports: [
        ReactiveFormsModule,
        RouterLink,
    ],
    templateUrl: './register.html',
    changeDetection:
        ChangeDetectionStrategy.OnPush,
})
export class Register {
    private readonly formBuilder =
        inject(FormBuilder);
    private readonly router =
        inject(Router);
    readonly authStore =
        inject(AuthStore);
    readonly form =
        this.formBuilder.nonNullable.group(
            {
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
                        Validators.maxLength(128),
                    ],
                ],
                confirmPassword: [
                    '',
                    [
                        Validators.required,
                    ],
                ],
            },
            {
                validators:
                    passwordsMatchValidator,
            },
        );

    async submit(): Promise<void> {
        this.authStore.clearError();

        if (this.form.invalid) {
            this.form.markAllAsTouched();
            return;
        }
        const {
            email,
            password,
        } = this.form.getRawValue();
        const success =
            await this.authStore.register({
                email,
                password,
            });
        if (!success) {
            return;
        }
        await this.authStore.loadCurrentUser();
        await this.router.navigate([
            '/projects',
        ]);
    }
}