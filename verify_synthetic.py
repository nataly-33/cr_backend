from apps.patients.models import Patient
from apps.clinical_records.models import ClinicalForm

# Obtener primer paciente sintético
p = Patient.objects.filter(identity_document__startswith='SYNTH-').first()
print(f'Paciente: {p.first_name} {p.last_name}')
print(f'Documento: {p.identity_document}')
print(f'Edad: {p.age} anos')
print(f'Genero: {p.gender}')

# Ver formularios clínicos
forms = ClinicalForm.objects.filter(clinical_record__patient=p)
print(f'\nFormularios clinicos: {forms.count()}')

for f in forms:
    print(f'\n  Tipo: {f.form_type}')
    print(f'  Campos: {list(f.form_data.keys())}')
    if f.form_type == 'triage':
        print(f'  Peso: {f.form_data.get("weight")} kg')
        print(f'  Altura: {f.form_data.get("height")} cm')
        print(f'  PA: {f.form_data.get("blood_pressure_systolic")}/{f.form_data.get("blood_pressure_diastolic")}')
    elif f.form_type == 'lab_order':
        print(f'  Test: {f.form_data.get("test_name")}')
        print(f'  Resultado: {f.form_data.get("result")}')

# Verificar historial familiar
cr = p.clinical_record
if cr.family_history:
    print(f'\nHistorial familiar: {cr.family_history}')
