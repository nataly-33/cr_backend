from apps.patients.models import Patient
from apps.clinical_records.models import ClinicalForm

# Obtener primer paciente sintético
patient = Patient.objects.filter(identity_document__startswith='SYNTH-').first()

# Ver todas las órdenes de laboratorio
lab_forms = ClinicalForm.objects.filter(
    clinical_record__patient=patient,
    form_type='lab_order'
).order_by('-form_date')

print(f'Paciente: {patient.first_name} {patient.last_name}')
print(f'Total lab orders: {lab_forms.count()}')
print()

for lab in lab_forms:
    print(f'Test: {lab.form_data.get("test_name")}')
    print(f'Resultado: {lab.form_data.get("result")}')
    print(f'Data completa: {lab.form_data}')
    print()
