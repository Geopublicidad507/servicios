#!/bin/bash
set -e

echo "🚀 Iniciando PH Control..."

# Función para verificar si PostgreSQL está listo
wait_for_postgres() {
    if [[ "$DATABASE_URL" == postgresql* ]]; then
        echo "⏳ Esperando PostgreSQL..."
        
        # Extraer detalles de conexión de DATABASE_URL
        # Formato: postgresql://user:pass@host:port/db
        DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
        DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
        DB_USER=$(echo $DATABASE_URL | sed -n 's/.*\/\/\([^:]*\):.*/\1/p')
        
        # Usar valores por defecto si no se pueden extraer
        DB_HOST=${DB_HOST:-ph-database}
        DB_PORT=${DB_PORT:-5432}
        DB_USER=${DB_USER:-phcontrol}
        
        # Esperar hasta que PostgreSQL esté listo
        echo "🔍 Verificando conexión a PostgreSQL..."
        echo "   Host: $DB_HOST"
        echo "   Puerto: $DB_PORT"
        echo "   Usuario: $DB_USER"
        
        until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -q; do
            echo "PostgreSQL no está listo - esperando..."
            sleep 3
        done
        
        echo "✅ PostgreSQL está listo!"
    fi
}

# Función de inicialización
initialize_system() {
    echo "🔧 Inicializando sistema..."
    
    # Ejecutar inicialización solo si no se ha saltado
    if [ "${SKIP_INIT:-false}" != "true" ]; then
        # Primero probar conexión simple
        echo "🧪 Probando conexión a la base de datos..."
        python init_simple.py
        
        if [ $? -eq 0 ]; then
            echo "✅ Conexión verificada, ejecutando inicialización completa..."
            python init_system.py
            
            if [ $? -eq 0 ]; then
                echo "✅ Sistema inicializado correctamente"
            else
                echo "❌ Error en inicialización completa"
                echo "🔄 Continuando sin inicialización..."
            fi
            
            # Verificar y corregir credenciales
            echo "🔧 Verificando credenciales de usuario..."
            python fix_admin_credentials.py
        else
            echo "❌ Error en conexión básica"
            echo "🔄 Continuando sin inicialización..."
        fi
    else
        echo "⏭️ Inicialización saltada (SKIP_INIT=true)"
    fi
}

# Función principal
main() {
    # Esperar PostgreSQL si es necesario
    wait_for_postgres
    
    # Inicializar sistema
    initialize_system
    
    echo "🌐 Iniciando aplicación Flask..."
    echo "Disponible en: http://localhost:${PORT:-5003}"
    
    # Iniciar aplicación
    exec python app.py
}

# Ejecutar función principal
main