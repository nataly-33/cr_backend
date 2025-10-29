import django_filters
from .models import Patient


class PatientFilter(django_filters.FilterSet):
    """Filtros avanzados para pacientes"""
    first_name = django_filters.CharFilter(lookup_expr='icontains')
    last_name = django_filters.CharFilter(lookup_expr='icontains')
    identity_document = django_filters.CharFilter(lookup_expr='icontains')
    gender = django_filters.ChoiceFilter(choices=Patient.GENDER_CHOICES)
    age_min = django_filters.NumberFilter(field_name='date_of_birth', lookup_expr='year__lte')
    age_max = django_filters.NumberFilter(field_name='date_of_birth', lookup_expr='year__gte')

    class Meta:
        model = Patient
        fields = ['gender', 'city']