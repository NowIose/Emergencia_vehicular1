import { ComponentFixture, TestBed } from '@angular/core/testing';

import { FacturacionServicios } from './facturacion-servicios';

describe('FacturacionServicios', () => {
  let component: FacturacionServicios;
  let fixture: ComponentFixture<FacturacionServicios>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [FacturacionServicios],
    }).compileComponents();

    fixture = TestBed.createComponent(FacturacionServicios);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
