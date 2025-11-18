#!/bin/bash
# Script de diagnóstico rápido para ejecutar en EC2

echo "=========================================="
echo "DIAGNÓSTICO RÁPIDO - CLINIC RECORDS"
echo "=========================================="
echo ""

cd /home/ubuntu/clinic_records/cr_backend || exit 1

echo "1️⃣  Verificando registraciones..."
echo "----------------------------------------"
sudo -u postgres psql -d clinidocs_db -c "SELECT id, admin_email, subdomain, status, activation_token IS NOT NULL as has_token FROM tenants_tenantregistration ORDER BY created_at DESC LIMIT 5;"
echo ""

echo "2️⃣  Verificando tenants..."
echo "----------------------------------------"
sudo -u postgres psql -d clinidocs_db -c "SELECT id, name, subdomain, email, subscription_status FROM core_tenant LIMIT 10;"
echo ""

echo "3️⃣  Verificando usuarios..."
echo "----------------------------------------"
sudo -u postgres psql -d clinidocs_db -c "SELECT u.id, u.email, u.personal_email, u.first_name, u.last_name, u.is_active, t.subdomain as tenant_subdomain FROM accounts_user u LEFT JOIN core_tenant t ON u.tenant_id = t.id LIMIT 10;"
echo ""

echo "4️⃣  Buscando usuario 'admin@clinica-virginia.com'..."
echo "----------------------------------------"
sudo -u postgres psql -d clinidocs_db -c "SELECT id, email, personal_email, is_active, tenant_id FROM accounts_user WHERE email LIKE '%clinica%' OR personal_email LIKE '%clinica%';"
echo ""

echo "5️⃣  Últimas líneas del log de Gunicorn..."
echo "----------------------------------------"
tail -30 /var/log/gunicorn/clinic_records.log
echo ""

echo "=========================================="
echo "FIN DEL DIAGNÓSTICO"
echo "=========================================="
