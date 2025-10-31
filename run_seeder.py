import sys
import io

# Configurar stdout con encoding UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Ejecutar el seeder
exec(open('scripts/seed_data.py', encoding='utf-8').read())
