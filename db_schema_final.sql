-- ============================================
-- SISTEMA DE GESTIÓN DOCUMENTAL - HISTORIAS CLÍNICAS
-- Versión 3.0 - Base de Datos Completa
-- Base de Datos: PostgreSQL 14+
-- Multi-tenant: SÍ
-- Stack: Django + React + Flutter + AWS
-- ============================================

-- Habilitar extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================
-- 1. PLANES DE SUSCRIPCIÓN Y PAGOS (STRIPE)
-- ============================================

CREATE TABLE subscription_plan (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE, -- Basic, Professional, Enterprise
    slug VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    price_monthly DECIMAL(10,2) NOT NULL,
    price_yearly DECIMAL(10,2),
    stripe_price_id VARCHAR(255),
    stripe_product_id VARCHAR(255),
    
    -- Límites del plan
    max_users INT NOT NULL DEFAULT 10,
    max_storage_gb INT NOT NULL DEFAULT 50,
    max_documents INT NOT NULL DEFAULT 1000,
    max_patients INT NOT NULL DEFAULT 500,
    
    -- Características del plan
    features JSONB NOT NULL DEFAULT '{}',
    
    is_active BOOLEAN DEFAULT true,
    is_popular BOOLEAN DEFAULT false,
    sort_order INT DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 2. TENANTS (HOSPITALES/CLÍNICAS)
-- ============================================

CREATE TABLE tenant (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Información básica
    name VARCHAR(255) NOT NULL,
    legal_name VARCHAR(255),
    subdomain VARCHAR(100) UNIQUE NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    
    -- Contacto
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    address TEXT,
    city VARCHAR(100),
    country VARCHAR(100) DEFAULT 'Bolivia',
    
    -- Estado del tenant
    status VARCHAR(50) DEFAULT 'trial', -- trial, active, suspended, cancelled
    trial_ends_at TIMESTAMP,
    
    -- Suscripción
    subscription_plan_id UUID REFERENCES subscription_plan(id),
    subscription_status VARCHAR(50),
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    
    -- Stripe IDs
    stripe_customer_id VARCHAR(255) UNIQUE,
    stripe_subscription_id VARCHAR(255),
    
    -- Uso y límites
    current_users_count INT DEFAULT 0,
    current_storage_bytes BIGINT DEFAULT 0,
    current_documents_count INT DEFAULT 0,
    current_patients_count INT DEFAULT 0,
    
    -- Configuración
    settings JSONB DEFAULT '{}',
    
    -- Metadata
    onboarding_completed BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    
    CONSTRAINT valid_subdomain CHECK (subdomain ~* '^[a-z0-9-]+$')
);

CREATE INDEX idx_tenant_subdomain ON tenant(subdomain) WHERE deleted_at IS NULL;
CREATE INDEX idx_tenant_status ON tenant(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_tenant_stripe_customer ON tenant(stripe_customer_id);

-- ============================================
-- 3. PAGOS Y FACTURACIÓN (STRIPE)
-- ============================================

CREATE TABLE payment (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD',
    status VARCHAR(50) NOT NULL, -- pending, succeeded, failed, refunded
    payment_method VARCHAR(50),
    
    -- Stripe IDs
    stripe_payment_intent_id VARCHAR(255),
    stripe_charge_id VARCHAR(255),
    stripe_invoice_id VARCHAR(255),
    
    description TEXT,
    metadata JSONB DEFAULT '{}',
    
    paid_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_payment_tenant ON payment(tenant_id);
CREATE INDEX idx_payment_status ON payment(status);

CREATE TABLE invoice (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    payment_id UUID REFERENCES payment(id),
    
    invoice_number VARCHAR(50) UNIQUE NOT NULL,
    
    -- Montos
    subtotal DECIMAL(10,2) NOT NULL,
    tax DECIMAL(10,2) DEFAULT 0,
    discount DECIMAL(10,2) DEFAULT 0,
    total DECIMAL(10,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'USD',
    
    status VARCHAR(50) DEFAULT 'draft',
    
    -- Stripe
    stripe_invoice_id VARCHAR(255),
    stripe_invoice_pdf VARCHAR(500),
    
    -- Fechas
    issue_date DATE NOT NULL,
    due_date DATE,
    paid_at TIMESTAMP,
    
    billing_details JSONB,
    line_items JSONB,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_invoice_tenant ON invoice(tenant_id);
CREATE INDEX idx_invoice_number ON invoice(invoice_number);

-- ============================================
-- 4. PERMISOS (POR TENANT)
-- ============================================

CREATE TABLE permission (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    
    -- Identificación del permiso
    name VARCHAR(100) NOT NULL, -- "Crear Usuario", "Eliminar Documento"
    slug VARCHAR(100) NOT NULL, -- "usuario.crear", "documento.eliminar"
    description TEXT,
    
    -- Categoría
    module VARCHAR(50) NOT NULL, -- usuario, documento, paciente, reporte, etc.
    action VARCHAR(50) NOT NULL, -- crear, leer, actualizar, eliminar, exportar
    
    -- Metadata
    is_system BOOLEAN DEFAULT false, -- Permisos del sistema (no editables)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_permission_slug_per_tenant UNIQUE(tenant_id, slug)
);

CREATE INDEX idx_permission_tenant ON permission(tenant_id);
CREATE INDEX idx_permission_module ON permission(module);

-- ============================================
-- 5. ROLES (POR TENANT)
-- ============================================

CREATE TABLE role (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    
    name VARCHAR(100) NOT NULL, -- "Doctor", "Enfermera", "Administrador"
    slug VARCHAR(100) NOT NULL, -- "doctor", "enfermera", "administrador"
    description TEXT,
    
    -- Tipo de rol
    is_system_role BOOLEAN DEFAULT false, -- Roles predefinidos
    is_default BOOLEAN DEFAULT false, -- Rol asignado por defecto
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_role_slug_per_tenant UNIQUE(tenant_id, slug)
);

CREATE INDEX idx_role_tenant ON role(tenant_id);

-- ============================================
-- 6. TABLA INTERMEDIA: ROLE - PERMISSION
-- ============================================

CREATE TABLE role_permission (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_id UUID NOT NULL REFERENCES role(id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES permission(id) ON DELETE CASCADE,
    
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    assigned_by UUID, -- FK a user (circular, nullable)
    
    CONSTRAINT unique_role_permission UNIQUE(role_id, permission_id)
);

CREATE INDEX idx_role_permission_role ON role_permission(role_id);
CREATE INDEX idx_role_permission_permission ON role_permission(permission_id);

-- ============================================
-- 7. USUARIOS
-- ============================================

CREATE TABLE "user" (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    role_id UUID REFERENCES role(id) ON DELETE SET NULL, -- UN SOLO ROL
    
    -- Credenciales
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    
    -- Información personal
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    full_name VARCHAR(255) GENERATED ALWAYS AS (first_name || ' ' || last_name) STORED,
    phone VARCHAR(50),
    avatar_url VARCHAR(500),
    
    -- Estado
    is_active BOOLEAN DEFAULT true,
    is_tenant_owner BOOLEAN DEFAULT false, -- Admin principal
    email_verified BOOLEAN DEFAULT false,
    
    -- Seguridad
    two_factor_enabled BOOLEAN DEFAULT false,
    two_factor_secret VARCHAR(255),
    password_reset_token VARCHAR(255),
    password_reset_expires TIMESTAMP,
    email_verification_token VARCHAR(255),
    email_verification_expires TIMESTAMP,
    
    -- Sesiones
    last_login TIMESTAMP,
    last_login_ip INET,
    failed_login_attempts INT DEFAULT 0,
    locked_until TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    
    CONSTRAINT unique_email_per_tenant UNIQUE(tenant_id, email)
);

CREATE INDEX idx_user_tenant ON "user"(tenant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_user_email ON "user"(email) WHERE deleted_at IS NULL;
CREATE INDEX idx_user_role ON "user"(role_id);
CREATE INDEX idx_user_tenant_owner ON "user"(tenant_id, is_tenant_owner) WHERE is_tenant_owner = true;

-- Agregar FK circular de role_permission.assigned_by
ALTER TABLE role_permission 
    ADD CONSTRAINT fk_role_permission_assigned_by 
    FOREIGN KEY (assigned_by) REFERENCES "user"(id) ON DELETE SET NULL;

-- ============================================
-- 8. PREFERENCIAS DE USUARIO
-- ============================================

CREATE TABLE user_preferences (
    user_id UUID PRIMARY KEY REFERENCES "user"(id) ON DELETE CASCADE,
    
    -- Apariencia
    theme VARCHAR(50) DEFAULT 'light',
    font_size VARCHAR(20) DEFAULT 'medium',
    
    -- Localización
    language VARCHAR(10) DEFAULT 'es',
    timezone VARCHAR(100) DEFAULT 'America/La_Paz',
    date_format VARCHAR(50) DEFAULT 'DD/MM/YYYY',
    time_format VARCHAR(50) DEFAULT 'HH:mm',
    
    -- Notificaciones
    notifications_enabled BOOLEAN DEFAULT true,
    email_notifications BOOLEAN DEFAULT true,
    push_notifications BOOLEAN DEFAULT true,
    
    preferences JSONB DEFAULT '{}',
    
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 9. PACIENTES
-- ============================================

CREATE TABLE patient (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    
    -- Identificación
    identity_document_type VARCHAR(50),
    identity_document VARCHAR(100) NOT NULL,
    
    -- Información personal
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    full_name VARCHAR(255) GENERATED ALWAYS AS (first_name || ' ' || last_name) STORED,
    date_of_birth DATE NOT NULL,
    gender VARCHAR(20),
    
    -- Contacto
    phone VARCHAR(50),
    email VARCHAR(255),
    address TEXT,
    city VARCHAR(100),
    
    -- Contacto de emergencia
    emergency_contact JSONB,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES "user"(id),
    deleted_at TIMESTAMP,
    
    CONSTRAINT unique_identity_per_tenant UNIQUE(tenant_id, identity_document)
);

CREATE INDEX idx_patient_tenant ON patient(tenant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_patient_identity ON patient(identity_document);
CREATE INDEX idx_patient_name ON patient(full_name);

-- ============================================
-- 10. HISTORIAS CLÍNICAS
-- ============================================

CREATE TABLE clinical_record (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    patient_id UUID NOT NULL REFERENCES patient(id) ON DELETE CASCADE,
    
    record_number VARCHAR(100) NOT NULL,
    
    status VARCHAR(50) DEFAULT 'active',
    
    -- Información clínica básica
    blood_type VARCHAR(10),
    allergies JSONB DEFAULT '[]',
    chronic_conditions JSONB DEFAULT '[]',
    medications JSONB DEFAULT '[]',
    family_history TEXT,
    social_history TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES "user"(id),
    
    CONSTRAINT unique_record_number_per_tenant UNIQUE(tenant_id, record_number)
);

CREATE INDEX idx_clinical_record_tenant ON clinical_record(tenant_id);
CREATE INDEX idx_clinical_record_patient ON clinical_record(patient_id);
CREATE INDEX idx_clinical_record_number ON clinical_record(record_number);

-- ============================================
-- 11. DOCUMENTOS CLÍNICOS (NÚCLEO)
-- ============================================

CREATE TABLE clinical_document (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    clinical_record_id UUID NOT NULL REFERENCES clinical_record(id) ON DELETE CASCADE,
    
    -- Tipo y clasificación
    document_type VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Información del documento
    document_date TIMESTAMP NOT NULL,
    specialty VARCHAR(100),
    doctor_name VARCHAR(255),
    doctor_license VARCHAR(100),
    
    -- Contenido estructurado
    content JSONB DEFAULT '{}',
    
    -- Archivo físico
    file_path VARCHAR(500),
    file_name VARCHAR(255),
    file_size_bytes BIGINT,
    mime_type VARCHAR(100),
    file_hash VARCHAR(64),
    
    -- OCR (Google Vision API)
    ocr_text TEXT,
    ocr_confidence DECIMAL(5,2),
    ocr_processed BOOLEAN DEFAULT false,
    
    -- Estado
    is_signed BOOLEAN DEFAULT false,
    signed_at TIMESTAMP,
    signed_by UUID REFERENCES "user"(id),
    digital_signature TEXT,
    
    is_locked BOOLEAN DEFAULT false,
    
    -- Metadata
    tags VARCHAR(100)[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES "user"(id),
    deleted_at TIMESTAMP
);

CREATE INDEX idx_clinical_document_tenant_record ON clinical_document(tenant_id, clinical_record_id);
CREATE INDEX idx_clinical_document_type ON clinical_document(document_type);
CREATE INDEX idx_clinical_document_date ON clinical_document(document_date DESC);
CREATE INDEX idx_clinical_document_specialty ON clinical_document(specialty);
CREATE INDEX idx_clinical_document_tags ON clinical_document USING GIN(tags);

-- ============================================
-- 12. ACCESO A DOCUMENTOS (TRACKING)
-- ============================================

CREATE TABLE document_access_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES clinical_document(id) ON DELETE CASCADE,
    user_id UUID REFERENCES "user"(id) ON DELETE SET NULL,
    
    -- Información del acceso
    access_type VARCHAR(50) NOT NULL, -- view, download, print, share
    user_email VARCHAR(255),
    user_name VARCHAR(255),
    
    -- Detalles técnicos
    ip_address INET,
    user_agent TEXT,
    
    -- Metadata
    access_reason TEXT, -- Opcional: justificación del acceso
    accessed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_document_access_tenant ON document_access_log(tenant_id);
CREATE INDEX idx_document_access_document ON document_access_log(document_id, accessed_at DESC);
CREATE INDEX idx_document_access_user ON document_access_log(user_id, accessed_at DESC);

-- ============================================
-- 13. IMÁGENES MÉDICAS (DICOM)
-- ============================================

CREATE TABLE medical_image (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    clinical_record_id UUID NOT NULL REFERENCES clinical_record(id) ON DELETE CASCADE,
    document_id UUID REFERENCES clinical_document(id),
    
    image_type VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    study_date TIMESTAMP NOT NULL,
    modality VARCHAR(50),
    body_part VARCHAR(100),
    
    -- Archivos
    file_path VARCHAR(500) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_size_bytes BIGINT,
    
    -- DICOM metadata
    dicom_metadata JSONB,
    
    -- AI Enhancement
    enhanced_image_path VARCHAR(500),
    enhancement_applied BOOLEAN DEFAULT false,
    enhancement_params JSONB,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES "user"(id),
    deleted_at TIMESTAMP
);

CREATE INDEX idx_medical_image_tenant_record ON medical_image(tenant_id, clinical_record_id);
CREATE INDEX idx_medical_image_type ON medical_image(image_type);
CREATE INDEX idx_medical_image_study_date ON medical_image(study_date DESC);

-- ============================================
-- 14. FORMULARIOS CLÍNICOS
-- ============================================

CREATE TABLE clinical_form (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    clinical_record_id UUID NOT NULL REFERENCES clinical_record(id) ON DELETE CASCADE,
    
    form_type VARCHAR(100) NOT NULL,
    form_template_id UUID,
    
    form_data JSONB NOT NULL,
    
    filled_by UUID NOT NULL REFERENCES "user"(id),
    doctor_name VARCHAR(255),
    doctor_specialty VARCHAR(100),
    
    form_date TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_clinical_form_tenant_record ON clinical_form(tenant_id, clinical_record_id);
CREATE INDEX idx_clinical_form_type ON clinical_form(form_type);
CREATE INDEX idx_clinical_form_date ON clinical_form(form_date DESC);

-- ============================================
-- 15. AUDITORÍA (CAJA NEGRA)
-- ============================================

CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenant(id) ON DELETE CASCADE,
    
    -- Usuario
    user_id UUID REFERENCES "user"(id) ON DELETE SET NULL,
    user_email VARCHAR(255),
    user_name VARCHAR(255),
    
    -- Acción
    action_type VARCHAR(100) NOT NULL,
    
    -- Recurso
    resource_type VARCHAR(100) NOT NULL,
    resource_id UUID,
    resource_name VARCHAR(255),
    
    -- Petición
    ip_address INET NOT NULL,
    user_agent TEXT,
    request_method VARCHAR(10),
    request_path VARCHAR(500),
    request_body JSONB,
    
    -- Cambios
    changes JSONB,
    
    -- Respuesta
    response_status INT,
    error_message TEXT,
    
    -- Contexto
    session_id UUID,
    metadata JSONB DEFAULT '{}',
    
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Hash inviolable
    log_hash VARCHAR(64)
);

CREATE INDEX idx_audit_log_tenant_time ON audit_log(tenant_id, timestamp DESC);
CREATE INDEX idx_audit_log_user ON audit_log(user_id, timestamp DESC);
CREATE INDEX idx_audit_log_resource ON audit_log(resource_type, resource_id);
CREATE INDEX idx_audit_log_action ON audit_log(action_type);
CREATE INDEX idx_audit_log_ip ON audit_log(ip_address);

-- ============================================
-- 16. REPORTES
-- ============================================

CREATE TABLE report_template (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenant(id) ON DELETE CASCADE,
    
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    report_type VARCHAR(100) NOT NULL,
    category VARCHAR(100),
    
    query_template TEXT,
    parameters JSONB DEFAULT '{}',
    
    output_formats VARCHAR(50)[] DEFAULT '{pdf,excel}',
    
    chart_config JSONB,
    
    is_public BOOLEAN DEFAULT false,
    allowed_roles UUID[],
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES "user"(id)
);

CREATE INDEX idx_report_template_tenant ON report_template(tenant_id);
CREATE INDEX idx_report_template_category ON report_template(category);

CREATE TABLE report_execution (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    template_id UUID REFERENCES report_template(id) ON DELETE SET NULL,
    
    executed_by UUID NOT NULL REFERENCES "user"(id),
    
    parameters_used JSONB,
    
    output_format VARCHAR(50),
    file_path VARCHAR(500),
    file_size_bytes BIGINT,
    
    execution_time_ms INT,
    rows_returned INT,
    
    status VARCHAR(50) DEFAULT 'completed',
    error_message TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_report_execution_tenant ON report_execution(tenant_id);
CREATE INDEX idx_report_execution_user ON report_execution(executed_by);
CREATE INDEX idx_report_execution_created ON report_execution(created_at DESC);

-- ============================================
-- 17. NOTIFICACIONES
-- ============================================

CREATE TABLE notification (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    
    notification_type VARCHAR(100) NOT NULL,
    priority VARCHAR(20) DEFAULT 'normal',
    
    related_resource_type VARCHAR(100),
    related_resource_id UUID,
    related_resource_url VARCHAR(500),
    
    is_read BOOLEAN DEFAULT false,
    read_at TIMESTAMP,
    
    push_sent BOOLEAN DEFAULT false,
    push_sent_at TIMESTAMP,
    push_token VARCHAR(255),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

CREATE INDEX idx_notification_user_unread ON notification(user_id, is_read, created_at DESC);
CREATE INDEX idx_notification_tenant ON notification(tenant_id);

-- ============================================
-- 18. BACKUPS
-- ============================================

CREATE TABLE backup_job (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenant(id) ON DELETE SET NULL,
    
    backup_type VARCHAR(50) NOT NULL,
    backup_scope VARCHAR(100) NOT NULL,
    
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    
    storage_location VARCHAR(500),
    backup_size_bytes BIGINT,
    
    includes_database BOOLEAN DEFAULT true,
    includes_files BOOLEAN DEFAULT true,
    includes_audit_logs BOOLEAN DEFAULT true,
    
    is_encrypted BOOLEAN DEFAULT true,
    encryption_key_id VARCHAR(255),
    
    scheduled BOOLEAN DEFAULT false,
    schedule_cron VARCHAR(100),
    
    can_restore BOOLEAN DEFAULT true,
    retention_until DATE,
    
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    error_message TEXT,
    retry_count INT DEFAULT 0,
    
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_backup_job_tenant ON backup_job(tenant_id);
CREATE INDEX idx_backup_job_status ON backup_job(status);
CREATE INDEX idx_backup_job_created ON backup_job(created_at DESC);

-- ============================================
-- 19. ESTADÍSTICAS Y ANALYTICS
-- ============================================

CREATE TABLE tenant_usage_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
    
    snapshot_date DATE NOT NULL,
    
    users_count INT DEFAULT 0,
    active_users_count INT DEFAULT 0,
    patients_count INT DEFAULT 0,
    clinical_records_count INT DEFAULT 0,
    documents_count INT DEFAULT 0,
    
    storage_bytes BIGINT DEFAULT 0,
    
    logins_count INT DEFAULT 0,
    documents_created INT DEFAULT 0,
    documents_viewed INT DEFAULT 0,
    reports_generated INT DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_tenant_snapshot UNIQUE(tenant_id, snapshot_date)
);

CREATE INDEX idx_tenant_usage_stats_tenant_date ON tenant_usage_stats(tenant_id, snapshot_date DESC);

-- ============================================
-- VISTAS ÚTILES
-- ============================================

-- Vista: Usuarios con sus roles y permisos
CREATE VIEW v_user_permissions AS
SELECT 
    u.id as user_id,
    u.tenant_id,
    u.email,
    u.full_name,
    u.is_tenant_owner,
    r.id as role_id,
    r.name as role_name,
    p.id as permission_id,
    p.name as permission_name,
    p.slug as permission_slug,
    p.module,
    p.action
FROM "user" u
LEFT JOIN role r ON u.role_id = r.id
LEFT JOIN role_permission rp ON r.id = rp.role_id
LEFT JOIN permission p ON rp.permission_id = p.id
WHERE u.deleted_at IS NULL;

-- Vista: Estadísticas por tenant
CREATE VIEW v_tenant_statistics AS
SELECT 
    t.id as tenant_id,
    t.name as tenant_name,
    t.status,
    sp.name as plan_name,
    COUNT(DISTINCT u.id) as total_users,
    COUNT(DISTINCT p.id) as total_patients,
    COUNT(DISTINCT cr.id) as total_clinical_records,
    COUNT(DISTINCT cd.id) as total_documents,
    COALESCE(SUM(cd.file_size_bytes), 0) as total_storage_bytes,
    ROUND(COALESCE(SUM(cd.file_size_bytes), 0)::numeric / 1073741824, 2) as total_storage_gb
FROM tenant t
LEFT JOIN subscription_plan sp ON t.subscription_plan_id = sp.id
LEFT JOIN "user" u ON t.id = u.tenant_id AND u.deleted_at IS NULL
LEFT JOIN patient p ON t.id = p.tenant_id AND p.deleted_at IS NULL
LEFT JOIN clinical_record cr ON t.id = cr.tenant_id
LEFT JOIN clinical_document cd ON t.id = cd.tenant_id AND cd.deleted_at IS NULL
WHERE t.deleted_at IS NULL
GROUP BY t.id, t.name, t.status, sp.name;

-- Vista: Documentos recientes por tenant
CREATE VIEW v_recent_documents AS
SELECT 
    cd.id,
    cd.tenant_id,
    cd.clinical_record_id,
    cd.document_type,
    cd.title,
    cd.document_date,
    cd.specialty,
    cd.doctor_name,
    p.full_name as patient_name,
    cr.record_number,
    u.full_name as created_by_name,
    cd.created_at
FROM clinical_document cd
JOIN clinical_record cr ON cd.clinical_record_id = cr.id
JOIN patient p ON cr.patient_id = p.id
LEFT JOIN "user" u ON cd.created_by = u.id
WHERE cd.deleted_at IS NULL
ORDER BY cd.created_at DESC;

-- ============================================
-- FUNCIONES ÚTILES
-- ============================================

-- Función: Obtener permisos de un usuario
CREATE OR REPLACE FUNCTION get_user_permissions(p_user_id UUID)
RETURNS TABLE(permission_slug TEXT) AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT p.slug::TEXT
    FROM "user" u
    JOIN role r ON u.role_id = r.id
    JOIN role_permission rp ON r.id = rp.role_id
    JOIN permission p ON rp.permission_id = p.id
    WHERE u.id = p_user_id
      AND u.deleted_at IS NULL;
END;
$$ LANGUAGE plpgsql;

-- Función: Verificar si usuario tiene permiso
--CREATE OR REPLACE FUNCTION user_has_permission(p_user_id UUID, p_permission_slug TEXT)
--RETURNS BOOLEAN AS $$
--BEGIN
--    RETURN EXISTS (
--        SELECT 1 FROM get_user_permissions(p_user_id) WHERE permission_slug = p_permission_slug
--    );
--END;
--$$