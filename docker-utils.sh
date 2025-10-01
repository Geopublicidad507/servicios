#!/bin/bash
# Utilidades para gestionar los contenedores Docker de PH Control

# Colores para mensajes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Función para mostrar el menú
show_menu() {
    echo -e "${CYAN}================ PH Control ================${NC}"
    echo "1. Iniciar contenedores"
    echo "2. Detener contenedores"
    echo "3. Reiniciar contenedores"
    echo "4. Ver logs"
    echo "5. Estado de contenedores"
    echo "6. Reconstruir contenedores"
    echo "7. Ejecutar pruebas"
    echo "8. Crear respaldo de base de datos"
    echo "9. Restaurar base de datos"
    echo "0. Salir"
    echo -e "${CYAN}=========================================${NC}"
}

# Función para iniciar contenedores
start_containers() {
    echo -e "${YELLOW}Iniciando contenedores...${NC}"
    docker-compose up -d
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Contenedores iniciados correctamente${NC}"
    else
        echo -e "${RED}❌ Error al iniciar contenedores${NC}"
    fi
}

# Función para detener contenedores
stop_containers() {
    echo -e "${YELLOW}Deteniendo contenedores...${NC}"
    docker-compose down
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Contenedores detenidos correctamente${NC}"
    else
        echo -e "${RED}❌ Error al detener contenedores${NC}"
    fi
}

# Función para reiniciar contenedores
restart_containers() {
    echo -e "${YELLOW}Reiniciando contenedores...${NC}"
    docker-compose restart
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Contenedores reiniciados correctamente${NC}"
    else
        echo -e "${RED}❌ Error al reiniciar contenedores${NC}"
    fi
}

# Función para ver logs
view_logs() {
    echo -e "${YELLOW}Mostrando logs (Ctrl+C para salir)...${NC}"
    docker-compose logs -f
}

# Función para ver estado de contenedores
container_status() {
    echo -e "${YELLOW}Estado de contenedores:${NC}"
    docker-compose ps
}

# Función para reconstruir contenedores
rebuild_containers() {
    echo -e "${YELLOW}Reconstruyendo contenedores...${NC}"
    docker-compose down
    docker-compose build
    docker-compose up -d
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Contenedores reconstruidos correctamente${NC}"
    else
        echo -e "${RED}❌ Error al reconstruir contenedores${NC}"
    fi
}

# Función para ejecutar pruebas
run_tests() {
    echo -e "${YELLOW}Ejecutando pruebas...${NC}"
    docker-compose exec ph-web pytest
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Pruebas completadas correctamente${NC}"
    else
        echo -e "${RED}❌ Algunas pruebas fallaron${NC}"
    fi
}

# Función para crear respaldo de base de datos
backup_database() {
    BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
    echo -e "${YELLOW}Creando respaldo de base de datos: $BACKUP_FILE${NC}"
    docker exec ph-control-database pg_dump -U phcontrol phcontrol_db > $BACKUP_FILE
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Respaldo creado correctamente: $BACKUP_FILE${NC}"
    else
        echo -e "${RED}❌ Error al crear respaldo${NC}"
    fi
}

# Función para restaurar base de datos
restore_database() {
    echo -e "${YELLOW}Archivos de respaldo disponibles:${NC}"
    ls -1 backup_*.sql 2>/dev/null
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ No se encontraron archivos de respaldo${NC}"
        return
    fi
    
    echo -e "${YELLOW}Ingrese el nombre del archivo de respaldo:${NC}"
    read BACKUP_FILE
    
    if [ ! -f "$BACKUP_FILE" ]; then
        echo -e "${RED}❌ Archivo no encontrado: $BACKUP_FILE${NC}"
        return
    fi
    
    echo -e "${YELLOW}Restaurando base de datos desde: $BACKUP_FILE${NC}"
    cat $BACKUP_FILE | docker exec -i ph-control-database psql -U phcontrol -d phcontrol_db
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Base de datos restaurada correctamente${NC}"
    else
        echo -e "${RED}❌ Error al restaurar la base de datos${NC}"
    fi
}

# Verificar si Docker está instalado
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker no está instalado o no está en el PATH${NC}"
    exit 1
fi

# Verificar si Docker Compose está instalado
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose no está instalado o no está en el PATH${NC}"
    exit 1
fi

# Bucle principal
while true; do
    show_menu
    echo -e "${YELLOW}Seleccione una opción:${NC}"
    read option
    
    case $option in
        1) start_containers ;;
        2) stop_containers ;;
        3) restart_containers ;;
        4) view_logs ;;
        5) container_status ;;
        6) rebuild_containers ;;
        7) run_tests ;;
        8) backup_database ;;
        9) restore_database ;;
        0) echo -e "${GREEN}¡Hasta pronto!${NC}"; exit 0 ;;
        *) echo -e "${RED}Opción inválida${NC}" ;;
    esac
    
    echo
    echo -e "${YELLOW}Presione Enter para continuar...${NC}"
    read
    clear
done