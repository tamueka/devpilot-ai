import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import {
    GeneratedUnitTests,
    GenerateUnitTestsRequest,
} from '@core/domain/unit-tests/unit-test.model';
import { UnitTestRepository } from '@core/domain/unit-tests/unit-test.repository';

@Injectable({
    providedIn: 'root',
})
export class GenerateUnitTestsUseCase {
    private readonly unitTestRepository = inject(
        UnitTestRepository,
    );

    execute(
        request: GenerateUnitTestsRequest,
    ): Observable<GeneratedUnitTests> {
        return this.unitTestRepository.generate(
            request,
        );
    }
}