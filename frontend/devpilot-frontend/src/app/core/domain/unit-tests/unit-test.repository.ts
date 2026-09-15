import { Observable } from 'rxjs';
import {
    GeneratedUnitTests,
    GenerateUnitTestsRequest,
    ProjectDocument,
} from '@core/domain/unit-tests/unit-test.model';

export abstract class UnitTestRepository {
    abstract getProjectDocuments(
        projectId: string,
    ): Observable<readonly ProjectDocument[]>;

    abstract generate(
        request: GenerateUnitTestsRequest,
    ): Observable<GeneratedUnitTests>;
}