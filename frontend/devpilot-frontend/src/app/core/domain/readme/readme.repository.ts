import { Observable } from 'rxjs';
import {
    GeneratedReadme,
    GenerateReadmeRequest,
} from '@core/domain/readme/readme.model';

export abstract class ReadmeRepository {
    abstract generate(
        request: GenerateReadmeRequest,
    ): Observable<GeneratedReadme>;
}