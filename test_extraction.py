from apps.patients.models import Patient
from apps.ai.services.diabetes_data_extractor import DiabetesDataExtractor

# Obtener primer paciente sintético
patient = Patient.objects.filter(identity_document__startswith='SYNTH-').first()

print(f'Extrayendo datos de: {patient.first_name} {patient.last_name}')
print(f'ID: {patient.id}')
print()

# Extraer features
features = DiabetesDataExtractor.extract_patient_features(str(patient.id))

print('Features extraídas:')
for key, value in features.items():
    print(f'  {key}: {value}')

print()
print('Array para modelo:')
array = DiabetesDataExtractor.features_to_array(features)
print(array)
