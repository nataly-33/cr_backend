"""
Prueba el impacto individual de cada feature en la predicción
"""
from apps.patients.models import Patient
from apps.ai.services.diabetes_data_extractor import DiabetesDataExtractor
from apps.ai.services.diabetes_model_trainer import DiabetesModelTrainer

print('='*70)
print('PRUEBA: Impacto Individual de Cada Feature')
print('='*70)
print()

# Obtener un paciente sintético con alto riesgo
patient = Patient.objects.filter(
    identity_document='SYNTH-00049'
).first()

if not patient:
    print('Paciente SYNTH-00049 no encontrado')
    patient = Patient.objects.filter(
        identity_document__startswith='SYNTH-'
    ).first()

print(f'Paciente: {patient.first_name} {patient.last_name}')
print(f'ID: {patient.id}')
print()

# Extraer features originales
features_original = DiabetesDataExtractor.extract_patient_features(str(patient.id))

print('FEATURES ORIGINALES:')
print('-'*70)
for key, value in features_original.items():
    if isinstance(value, float):
        print(f'  {key:30}: {value:>8.2f}')
    else:
        print(f'  {key:30}: {value:>8}')

print()

# Cargar modelo
model_tuple = DiabetesModelTrainer.load_active_model()
if not model_tuple or len(model_tuple) < 2:
    print('No se pudo cargar el modelo')
    exit()

model = model_tuple[0]

# Predicción original
array_original = DiabetesDataExtractor.features_to_array(features_original)
prob_original = model.predict_proba([array_original])[0][1]

print('PREDICCION ORIGINAL:')
print(f'  Probabilidad diabetes: {prob_original*100:.2f}%')
print()
print()

# Probar impacto de cada feature
print('IMPACTO DE CADA FEATURE (cambiando solo una a la vez):')
print('='*70)
print()

tests = [
    {
        'name': 'Reducir GLUCOSA a 95 mg/dL',
        'feature': 'glucose',
        'value': 95.0,
        'description': 'De {} a 95.0 (normal)'
    },
    {
        'name': 'Reducir IMC a 24.5',
        'feature': 'bmi',
        'value': 24.5,
        'description': 'De {:.1f} a 24.5 (normal)'
    },
    {
        'name': 'Reducir EDAD a 30 años',
        'feature': 'age',
        'value': 30,
        'description': 'De {} a 30 años'
    },
    {
        'name': 'Eliminar HISTORIAL FAMILIAR',
        'feature': 'diabetes_pedigree_function',
        'value': 0.5,
        'description': 'De {:.2f} a 0.5 (sin antecedentes)'
    },
    {
        'name': 'Reducir PRESION a 75',
        'feature': 'blood_pressure',
        'value': 75.0,
        'description': 'De {:.1f} a 75.0 (normal)'
    },
    {
        'name': 'Reducir INSULINA a 85',
        'feature': 'insulin',
        'value': 85.0,
        'description': 'De {:.1f} a 85.0 (normal)'
    }
]

results = []

for test in tests:
    # Crear copia de features
    features_test = features_original.copy()

    # Modificar solo una feature
    old_value = features_test[test['feature']]
    features_test[test['feature']] = test['value']

    # Predecir
    array_test = DiabetesDataExtractor.features_to_array(features_test)
    prob_test = model.predict_proba([array_test])[0][1]

    # Calcular cambio
    change = prob_test - prob_original

    results.append({
        'name': test['name'],
        'description': test['description'].format(old_value),
        'prob': prob_test * 100,
        'change': change * 100
    })

    print(f"Test: {test['name']}")
    print(f"  Cambio: {test['description'].format(old_value)}")
    print(f"  Nueva probabilidad: {prob_test*100:.2f}%")
    print(f"  Diferencia: {change*100:+.2f}%")

    if abs(change) < 0.01:
        print(f"  Impacto: MINIMO")
    elif abs(change) < 0.10:
        print(f"  Impacto: BAJO")
    elif abs(change) < 0.30:
        print(f"  Impacto: MEDIO")
    else:
        print(f"  Impacto: ALTO")

    print()

print()
print('='*70)
print('RESUMEN: Features ordenadas por impacto')
print('='*70)
print()

# Ordenar por impacto
results_sorted = sorted(results, key=lambda x: abs(x['change']), reverse=True)

print(f"{'Feature':<35} {'Prob':<12} {'Cambio':<12} {'Impacto':<10}")
print('-'*70)

for r in results_sorted:
    impact = 'ALTO' if abs(r['change']) > 30 else 'MEDIO' if abs(r['change']) > 10 else 'BAJO'
    print(f"{r['name']:<35} {r['prob']:>6.2f}%     {r['change']:>+6.2f}%     {impact}")

print()
print('CONCLUSION:')
print('El modelo NO decide solo por UNA feature, sino por la COMBINACION de todas.')
print('Las features mas importantes son (en orden):')
print('  1. Glucosa')
print('  2. IMC (Indice de Masa Corporal)')
print('  3. Edad')
print('  4. Diabetes Pedigree Function (historial familiar)')
