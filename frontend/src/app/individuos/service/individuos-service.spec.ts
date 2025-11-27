import { TestBed } from '@angular/core/testing';

import { IndividuosService } from './individuos-service';

describe('IndividuoService', () => {
  let service: IndividuosService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(IndividuosService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
