"""
Sistema de templates para notificaciones.

Permite renderizar títulos y cuerpos con variables.
Soporta múltiples idiomas (ES/EN).
"""

from typing import Dict, Any, Optional


class NotificationTemplate:
    """Plantilla de notificación con soporté para variables."""
    
    def __init__(
        self,
        notification_type: str,
        title_es: str,
        body_es: str,
        title_en: str,
        body_en: str,
        required_variables: list = None,
        icon: str = None,
        color: str = None,
    ):
        self.notification_type = notification_type
        self.title_es = title_es
        self.body_es = body_es
        self.title_en = title_en
        self.body_en = body_en
        self.required_variables = required_variables or []
        self.icon = icon or 'bell'
        self.color = color or 'blue'
    
    def render(
        self,
        language: str = 'es',
        variables: Dict[str, Any] = None,
    ) -> tuple[str, str]:
        """
        Renderizar título y cuerpo con variables.
        
        Args:
            language: 'es' o 'en'
            variables: dict con variables a reemplazar
        
        Returns:
            (title, body) después de reemplazar variables
        """
        variables = variables or {}
        
        # Seleccionar idioma
        title = self.title_es if language == 'es' else self.title_en
        body = self.body_es if language == 'es' else self.body_en
        
        # Validar variables requeridas
        for var in self.required_variables:
            if var not in variables:
                raise ValueError(f"Variable requerida faltante: {var}")
        
        # Reemplazar variables
        for key, value in variables.items():
            title = title.replace(f'{{{{{key}}}}}', str(value))
            body = body.replace(f'{{{{{key}}}}}', str(value))
        
        # Limitar longitudes
        title = title[:70]
        body = body[:300]
        
        return title, body


# Registro de templates
NOTIFICATION_TEMPLATES = {
    # Citas
    'appointment.created': NotificationTemplate(
        notification_type='appointment.created',
        title_es='Nueva cita programada',
        body_es='Cita de {{patient_name}} con {{doctor_name}} el {{appointment_date}} a las {{appointment_time}}',
        title_en='New appointment scheduled',
        body_en='Appointment for {{patient_name}} with {{doctor_name}} on {{appointment_date}} at {{appointment_time}}',
        required_variables=['patient_name', 'doctor_name', 'appointment_date', 'appointment_time'],
        icon='calendar',
        color='blue',
    ),
    
    'appointment.canceled': NotificationTemplate(
        notification_type='appointment.canceled',
        title_es='Cita cancelada',
        body_es='La cita de {{patient_name}} con {{doctor_name}} el {{appointment_date}} ha sido cancelada',
        title_en='Appointment canceled',
        body_en='The appointment for {{patient_name}} with {{doctor_name}} on {{appointment_date}} has been canceled',
        required_variables=['patient_name', 'doctor_name', 'appointment_date'],
        icon='x-circle',
        color='red',
    ),
    
    'appointment.reminder': NotificationTemplate(
        notification_type='appointment.reminder',
        title_es='Recordatorio de cita',
        body_es='{{patient_name}}, recordatorio: cita con {{doctor_name}} hoy a las {{appointment_time}}',
        title_en='Appointment reminder',
        body_en='{{patient_name}}, reminder: appointment with {{doctor_name}} today at {{appointment_time}}',
        required_variables=['patient_name', 'doctor_name', 'appointment_time'],
        icon='clock',
        color='yellow',
    ),
    
    # Resultados clínicos
    'clinical_record.result': NotificationTemplate(
        notification_type='clinical_record.result',
        title_es='Resultado clínico disponible',
        body_es='Nuevo resultado de {{test_type}} para {{patient_name}} del Dr. {{doctor_name}}',
        title_en='Clinical result available',
        body_en='New {{test_type}} result for {{patient_name}} from Dr. {{doctor_name}}',
        required_variables=['patient_name', 'doctor_name', 'test_type'],
        icon='check-circle',
        color='green',
    ),
    
    # Documentos
    'document.uploaded': NotificationTemplate(
        notification_type='document.uploaded',
        title_es='Nuevo documento cargado',
        body_es='{{document_type}} para {{patient_name}} cargado por {{uploaded_by}}',
        title_en='New document uploaded',
        body_en='{{document_type}} for {{patient_name}} uploaded by {{uploaded_by}}',
        required_variables=['patient_name', 'document_type', 'uploaded_by'],
        icon='file-text',
        color='purple',
    ),
    
    # Stock
    'inventory.low_stock': NotificationTemplate(
        notification_type='inventory.low_stock',
        title_es='Stock bajo: {{item_name}}',
        body_es='{{item_name}} tiene {{current_stock}} unidades (mínimo: {{min_stock}})',
        title_en='Low stock: {{item_name}}',
        body_en='{{item_name}} has {{current_stock}} units (minimum: {{min_stock}})',
        required_variables=['item_name', 'current_stock', 'min_stock'],
        icon='alert-triangle',
        color='orange',
    ),
    
    # Usuarios
    'user.added': NotificationTemplate(
        notification_type='user.added',
        title_es='Nuevo usuario agregado',
        body_es='{{user_name}} ({{user_email}}) ha sido agregado como {{user_role}}',
        title_en='New user added',
        body_en='{{user_name}} ({{user_email}}) has been added as {{user_role}}',
        required_variables=['user_name', 'user_email', 'user_role'],
        icon='user-plus',
        color='green',
    ),
    
    # Sistema
    'system.alert': NotificationTemplate(
        notification_type='system.alert',
        title_es='{{alert_title}}',
        body_es='{{alert_message}}',
        title_en='{{alert_title}}',
        body_en='{{alert_message}}',
        required_variables=['alert_title', 'alert_message'],
        icon='alert-circle',
        color='red',
    ),
    
    # Documentos CRUD
    'document.created': NotificationTemplate(
        notification_type='document.created',
        title_es='📄 Documento creado',
        body_es='{{actor_name}} creó "{{document_title}}" ({{document_type}}) para {{patient_name}}',
        title_en='📄 Document created',
        body_en='{{actor_name}} created "{{document_title}}" ({{document_type}}) for {{patient_name}}',
        required_variables=['actor_name', 'document_title', 'document_type', 'patient_name'],
        icon='file-plus',
        color='green',
    ),
    
    'document.updated': NotificationTemplate(
        notification_type='document.updated',
        title_es='📝 Documento actualizado',
        body_es='{{actor_name}} actualizó "{{document_title}}" ({{document_type}}) de {{patient_name}}',
        title_en='📝 Document updated',
        body_en='{{actor_name}} updated "{{document_title}}" ({{document_type}}) for {{patient_name}}',
        required_variables=['actor_name', 'document_title', 'document_type', 'patient_name'],
        icon='edit',
        color='blue',
    ),
    
    'document.deleted': NotificationTemplate(
        notification_type='document.deleted',
        title_es='🗑️ Documento eliminado',
        body_es='⚠️ {{actor_name}} eliminó "{{document_title}}" ({{document_type}}) de {{patient_name}}',
        title_en='🗑️ Document deleted',
        body_en='⚠️ {{actor_name}} deleted "{{document_title}}" ({{document_type}}) for {{patient_name}}',
        required_variables=['actor_name', 'document_title', 'document_type', 'patient_name'],
        icon='trash-2',
        color='red',
    ),
    
    # Clinical Records CRUD
    'clinical_record.created': NotificationTemplate(
        notification_type='clinical_record.created',
        title_es='📋 Historia clínica creada',
        body_es='{{actor_name}} creó la historia clínica #{{record_number}} para {{patient_name}}',
        title_en='📋 Clinical record created',
        body_en='{{actor_name}} created clinical record #{{record_number}} for {{patient_name}}',
        required_variables=['actor_name', 'record_number', 'patient_name'],
        icon='clipboard',
        color='green',
    ),
    
    'clinical_record.updated': NotificationTemplate(
        notification_type='clinical_record.updated',
        title_es='📝 Historia clínica actualizada',
        body_es='{{actor_name}} actualizó la historia #{{record_number}} de {{patient_name}} ({{status}})',
        title_en='📝 Clinical record updated',
        body_en='{{actor_name}} updated record #{{record_number}} for {{patient_name}} ({{status}})',
        required_variables=['actor_name', 'record_number', 'patient_name', 'status'],
        icon='edit-3',
        color='blue',
    ),
    
    'clinical_record.deleted': NotificationTemplate(
        notification_type='clinical_record.deleted',
        title_es='🚨 Historia clínica eliminada',
        body_es='⚠️ CRÍTICO: {{actor_name}} eliminó la historia #{{record_number}} de {{patient_name}}',
        title_en='🚨 Clinical record deleted',
        body_en='⚠️ CRITICAL: {{actor_name}} deleted record #{{record_number}} for {{patient_name}}',
        required_variables=['actor_name', 'record_number', 'patient_name'],
        icon='alert-octagon',
        color='red',
    ),
    
    # Clinical Forms CRUD
    'clinical_form.created': NotificationTemplate(
        notification_type='clinical_form.created',
        title_es='📝 Formulario clínico creado',
        body_es='{{actor_name}} creó un formulario {{form_type}} para {{patient_name}} (HC: {{clinical_record}})',
        title_en='📝 Clinical form created',
        body_en='{{actor_name}} created a {{form_type}} form for {{patient_name}} (CR: {{clinical_record}})',
        required_variables=['actor_name', 'form_type', 'patient_name', 'clinical_record'],
        icon='file-text',
        color='green',
    ),
    
    'clinical_form.updated': NotificationTemplate(
        notification_type='clinical_form.updated',
        title_es='✏️ Formulario clínico actualizado',
        body_es='{{actor_name}} actualizó el formulario {{form_type}} de {{patient_name}}',
        title_en='✏️ Clinical form updated',
        body_en='{{actor_name}} updated the {{form_type}} form for {{patient_name}}',
        required_variables=['actor_name', 'form_type', 'patient_name'],
        icon='edit',
        color='blue',
    ),
    
    'clinical_form.deleted': NotificationTemplate(
        notification_type='clinical_form.deleted',
        title_es='🗑️ Formulario clínico eliminado',
        body_es='⚠️ {{actor_name}} eliminó el formulario {{form_type}} de {{patient_name}} (HC: {{clinical_record}})',
        title_en='🗑️ Clinical form deleted',
        body_en='⚠️ {{actor_name}} deleted the {{form_type}} form for {{patient_name}} (CR: {{clinical_record}})',
        required_variables=['actor_name', 'form_type', 'patient_name', 'clinical_record'],
        icon='x-square',
        color='red',
    ),
}


def get_template(notification_type: str) -> Optional[NotificationTemplate]:
    """Obtener template por tipo de notificación."""
    return NOTIFICATION_TEMPLATES.get(notification_type)


def render_notification(
    notification_type: str,
    language: str = 'es',
    variables: Dict[str, Any] = None,
) -> tuple[str, str, Optional[str], Optional[str]]:
    """
    Renderizar una notificación completa.
    
    Args:
        notification_type: tipo de notificación
        language: 'es' o 'en'
        variables: variables para renderizar
    
    Returns:
        (title, body, icon, color)
    
    Raises:
        ValueError si el tipo no existe o faltan variables
    """
    template = get_template(notification_type)
    if not template:
        raise ValueError(f"Tipo de notificación no conocido: {notification_type}")
    
    title, body = template.render(language=language, variables=variables)
    return title, body, template.icon, template.color
