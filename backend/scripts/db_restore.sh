#!/bin/bash
# Script para restaurar backup de base de datos
# Lee credenciales desde .env

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Obtener directorio del script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$BACKEND_DIR/.env"

# Verificar que existe .env
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: No se encontró .env en $BACKEND_DIR${NC}"
    exit 1
fi

# Cargar variables de .env
export $(grep -v '^#' "$ENV_FILE" | xargs)

# Variables de BD
DB_NAME="${DB_NAME:-kaila}"
DB_USER="${DB_USER:-root}"
DB_PASSWORD="${DB_PASSWORD:-}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-3306}"

# Ruta de MySQL
MYSQL_PATH="/usr/local/mysql-9.5.0-macos15-arm64/bin"
export DYLD_LIBRARY_PATH="/usr/local/mysql-9.5.0-macos15-arm64/lib:$DYLD_LIBRARY_PATH"

# Función para ejecutar MySQL
mysql_exec() {
    "$MYSQL_PATH/mysql" -u "$DB_USER" -p"$DB_PASSWORD" -h "$DB_HOST" -P "$DB_PORT" "$@"
}

mysql_dump() {
    "$MYSQL_PATH/mysqldump" -u "$DB_USER" -p"$DB_PASSWORD" -h "$DB_HOST" -P "$DB_PORT" "$@"
}

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}   Restaurador de Base de Datos${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""
echo -e "BD: ${GREEN}$DB_NAME${NC} @ ${GREEN}$DB_HOST:$DB_PORT${NC}"
echo ""

# Verificar argumento
if [ -z "$1" ]; then
    echo -e "${YELLOW}Uso:${NC}"
    echo "  $0 <archivo_backup.sql>    - Restaurar desde backup"
    echo "  $0 --clear                 - Solo limpiar BD (sin restaurar)"
    echo "  $0 --list                  - Listar backups disponibles"
    echo ""

    # Mostrar backups disponibles
    BACKUP_DIR="$BACKEND_DIR/../backups"
    if [ -d "$BACKUP_DIR" ]; then
        echo -e "${YELLOW}Backups disponibles:${NC}"
        ls -lh "$BACKUP_DIR"/*.sql 2>/dev/null || echo "  (ninguno)"
    fi
    exit 1
fi

# Opción --list
if [ "$1" == "--list" ]; then
    BACKUP_DIR="$BACKEND_DIR/../backups"
    echo -e "${YELLOW}Backups disponibles:${NC}"
    ls -lh "$BACKUP_DIR"/*.sql 2>/dev/null || echo "  (ninguno)"
    exit 0
fi

# Confirmar acción
echo -e "${RED}⚠️  ADVERTENCIA: Esto eliminará TODOS los datos de la BD '$DB_NAME'${NC}"
read -p "¿Continuar? (escribe 'SI' para confirmar): " confirm

if [ "$confirm" != "SI" ]; then
    echo -e "${YELLOW}Operación cancelada${NC}"
    exit 0
fi

echo ""
echo -e "${YELLOW}[1/3] Eliminando tablas existentes...${NC}"

# Obtener lista de tablas y eliminarlas
TABLES=$(mysql_exec -N -e "SELECT GROUP_CONCAT(table_name) FROM information_schema.tables WHERE table_schema='$DB_NAME';" 2>/dev/null)

if [ -n "$TABLES" ] && [ "$TABLES" != "NULL" ]; then
    mysql_exec -e "SET FOREIGN_KEY_CHECKS=0;" "$DB_NAME" 2>/dev/null

    # Eliminar cada tabla
    IFS=',' read -ra TABLE_ARRAY <<< "$TABLES"
    for table in "${TABLE_ARRAY[@]}"; do
        echo "  Eliminando: $table"
        mysql_exec -e "DROP TABLE IF EXISTS \`$table\`;" "$DB_NAME" 2>/dev/null
    done

    mysql_exec -e "SET FOREIGN_KEY_CHECKS=1;" "$DB_NAME" 2>/dev/null
    echo -e "${GREEN}  ✓ Tablas eliminadas${NC}"
else
    echo -e "${GREEN}  ✓ BD ya está vacía${NC}"
fi

# Si solo queremos limpiar
if [ "$1" == "--clear" ]; then
    echo ""
    echo -e "${GREEN}✅ Base de datos limpiada exitosamente${NC}"
    exit 0
fi

# Verificar que existe el archivo de backup
BACKUP_FILE="$1"

# Si es ruta relativa, buscar en backups
if [ ! -f "$BACKUP_FILE" ]; then
    BACKUP_DIR="$BACKEND_DIR/../backups"
    if [ -f "$BACKUP_DIR/$BACKUP_FILE" ]; then
        BACKUP_FILE="$BACKUP_DIR/$BACKUP_FILE"
    else
        echo -e "${RED}Error: No se encontró el archivo: $1${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${YELLOW}[2/3] Importando backup...${NC}"
echo "  Archivo: $BACKUP_FILE"
echo "  Tamaño: $(ls -lh "$BACKUP_FILE" | awk '{print $5}')"

mysql_exec "$DB_NAME" < "$BACKUP_FILE" 2>/dev/null

echo -e "${GREEN}  ✓ Backup importado${NC}"

echo ""
echo -e "${YELLOW}[3/3] Verificando...${NC}"
TABLE_COUNT=$(mysql_exec -N -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='$DB_NAME';" 2>/dev/null)
echo -e "  Tablas creadas: ${GREEN}$TABLE_COUNT${NC}"

echo ""
echo -e "${GREEN}✅ Restauración completada exitosamente${NC}"
