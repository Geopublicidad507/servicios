#!/bin/bash
set -e

echo "🚀 Iniciando PH Control..."

# Función para verificar si MongoDB está listo
wait_for_mongo() {
    if [[ "$MONGO_URI" == mongodb* ]]; then
        echo "⏳ Esperando MongoDB..."

        # Extraer detalles de conexión de MONGO_URI
        # Formato: mongodb://host:port/database
        DB_HOST=$(echo $MONGO_URI | sed -n 's/mongodb:\/\/\([^:]*\):.*/\1/p')
        DB_PORT=$(echo $MONGO_URI | sed -n 's/mongodb:\/\/[^:]*:\([0-9]*\).*/\1/p')

        # Usar valores por defecto si no se pueden extraer
        DB_HOST=${DB_HOST:-ph-database}
        DB_PORT=${DB_PORT:-27017}

        # Esperar hasta que MongoDB esté listo
        echo "🔍 Verificando conexión a MongoDB..."
        echo "   Host: $DB_HOST"
        echo "   Puerto: $DB_PORT"

        until mongosh --host "$DB_HOST" --port "$DB_PORT" --eval "db.adminCommand('ping')" --quiet; do
            echo "MongoDB no está listo - esperando..."
            sleep 3
        done

        echo "✅ MongoDB está listo!"
    fi
}

# Función de inicialización
initialize_system() {
    echo "🔧 Inicializando sistema..."

    # Ejecutar inicialización solo si no se ha saltado
    if [ "${SKIP_INIT:-false}" != "true" ]; then
        # Ejecutar inicialización de MongoDB
        echo "🧪 Probando conexión a MongoDB e inicializando datos..."
        python init_mongo.py

        if [ $? -eq 0 ]; then
            echo "✅ Sistema inicializado correctamente con MongoDB"
        else
            echo "❌ Error en inicialización de MongoDB"
            echo "🔄 Continuando sin inicialización..."
        fi
    else
        echo "⏭️ Inicialización saltada (SKIP_INIT=true)"
    fi
}

# Función principal
main() {
    # Esperar MongoDB si es necesario
    wait_for_mongo

    # Inicializar sistema
    initialize_system

    echo "🌐 Iniciando aplicación Flask..."
    echo "Disponible en: http://localhost:${PORT:-5003}"

    # Iniciar aplicación
    exec python app.py
}

# Ejecutar función principal
main