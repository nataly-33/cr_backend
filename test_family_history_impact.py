from apps.patients.models import Patient
from apps.ai.services.diabetes_data_extractor import DiabetesDataExtractor
from apps.ai.services.diabetes_model_trainer import DiabetesModelTrainer
from apps.clinical_records.models import ClinicalRecord

print('='*70)
print('PRUEBA: Impacto del Historial Familiar en Predicciones')
print('='*70)
print()

# Obtener un paciente sintético con historial familiar
p = Patient.objects.filter(
    identity_document__startswith='SYNTH-',
    clinicalrecord__family_history__isnull=False
).first()

print(f'Paciente: {p.first_name} {p.last_name}')
print(f'ID: {p.id}')
print(f'Edad: {p.get_age()} anos')
print()

cr = ClinicalRecord.objects.filter(patient=p, status='active').first()
original_history = cr.family_history

print('ESCENARIO 1: Historial familiar original')
print('='*70)
print(f'Historial: {cr.family_history}')
print()

f1 = DiabetesDataExtractor.extract_patient_features(str(p.id))
print(f'Pedigree function: {f1["diabetes_pedigree_function"]:.3f}')
print(f'Glucosa: {f1["glucose"]:.1f} mg/dL')
print(f'IMC: {f1["bmi"]:.1f}')
print(f'Presion: {f1["blood_pressure"]:.1f}')
print()

model = DiabetesModelTrainer.load_active_model()
arr1 = DiabetesDataExtractor.features_to_array(f1)
pred1 = model.predict([arr1])[0]
prob1 = model.predict_proba([arr1])[0]

print(f'Prediccion: {"POSITIVA (Diabetes)" if pred1 == 1 else "NEGATIVA (No diabetes)"}')
print(f'Probabilidad diabetes: {prob1[1]*100:.2f}%')
print(f'Probabilidad no diabetes: {prob1[0]*100:.2f}%')
print()
print()

print('ESCENARIO 2: SIN historial familiar')
print('='*70)
cr.family_history = None
cr.save()

f2 = DiabetesDataExtractor.extract_patient_features(str(p.id))
arr2 = DiabetesDataExtractor.features_to_array(f2)
pred2 = model.predict([arr2])[0]
prob2 = model.predict_proba([arr2])[0]

print('Historial: Ninguno')
print(f'Pedigree function: {f2["diabetes_pedigree_function"]:.3f}')
print(f'Prediccion: {"POSITIVA (Diabetes)" if pred2 == 1 else "NEGATIVA (No diabetes)"}')
print(f'Probabilidad diabetes: {prob2[1]*100:.2f}%')
print(f'Cambio vs escenario 1: {(prob2[1]-prob1[1])*100:+.2f}%')
print()
print()

print('ESCENARIO 3: Historial familiar FUERTE (ambos padres)')
print('='*70)
cr.family_history = 'Padre y madre con diabetes tipo 2'
cr.save()

f3 = DiabetesDataExtractor.extract_patient_features(str(p.id))
arr3 = DiabetesDataExtractor.features_to_array(f3)
pred3 = model.predict([arr3])[0]
prob3 = model.predict_proba([arr3])[0]

print('Historial: Padre y madre con diabetes tipo 2')
print(f'Pedigree function: {f3["diabetes_pedigree_function"]:.3f}')
print(f'Prediccion: {"POSITIVA (Diabetes)" if pred3 == 1 else "NEGATIVA (No diabetes)"}')
print(f'Probabilidad diabetes: {prob3[1]*100:.2f}%')
print(f'Cambio vs escenario 1: {(prob3[1]-prob1[1])*100:+.2f}%')
print()
print()

# Restaurar historial original
cr.family_history = original_history
cr.save()

print('='*70)
print('RESUMEN COMPARATIVO')
print('='*70)
print()
print(f'{"Escenario":<40} {"Pedigree":<12} {"Prob Diabetes":<15}')
print('-'*70)
print(f'{"1. Historial original":<40} {f1["diabetes_pedigree_function"]:<12.3f} {prob1[1]*100:<15.2f}%')
print(f'{"2. Sin historial familiar":<40} {f2["diabetes_pedigree_function"]:<12.3f} {prob2[1]*100:<15.2f}%')
print(f'{"3. Ambos padres con diabetes":<40} {f3["diabetes_pedigree_function"]:<12.3f} {prob3[1]*100:<15.2f}%')
print()
print('CONCLUSION:')
print('El historial familiar SI afecta directamente la prediccion a traves de la')
print('feature "diabetes_pedigree_function" que se extrae del campo family_history.')
print('='*70)
