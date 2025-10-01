-- Inicialización de la base de datos para PH Control
-- Este script se ejecuta automáticamente al iniciar el contenedor PostgreSQL

-- Crear extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "unaccent";

-- Configurar zona horaria
SET timezone = 'America/Panama';

-- Crear índices para búsqueda de texto
CREATE INDEX IF NOT EXISTS idx_users_email ON users USING gin (email gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_properties_name ON properties USING gin (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_properties_code ON properties USING gin (code gin_trgm_ops);

-- Crear funciones de búsqueda
CREATE OR REPLACE FUNCTION search_properties(search_term TEXT)
RETURNS TABLE (
    id INTEGER,
    name TEXT,
    code TEXT,
    address TEXT,
    total_units INTEGER,
    admin_id INTEGER,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id, 
        p.name, 
        p.code, 
        p.address, 
        p.total_units, 
        p.admin_id,
        similarity(p.name, search_term) AS sim
    FROM 
        properties p
    WHERE 
        p.name ILIKE '%' || search_term || '%' OR
        p.code ILIKE '%' || search_term || '%' OR
        p.address ILIKE '%' || search_term || '%'
    ORDER BY 
        sim DESC;
END;
$$ LANGUAGE plpgsql;

-- Crear vistas para reportes comunes
CREATE OR REPLACE VIEW financial_summary AS
SELECT 
    p.id AS property_id,
    p.name AS property_name,
    p.code AS property_code,
    EXTRACT(YEAR FROM payment_date) AS year,
    EXTRACT(MONTH FROM payment_date) AS month,
    SUM(CASE WHEN py.status = 'paid' THEN py.amount ELSE 0 END) AS income,
    COUNT(DISTINCT py.id) AS payment_count,
    COUNT(DISTINCT u.id) AS unit_count
FROM 
    properties p
    LEFT JOIN units u ON p.id = u.property_id
    LEFT JOIN payments py ON u.id = py.unit_id
GROUP BY 
    p.id, p.name, p.code, year, month;

CREATE OR REPLACE VIEW expense_summary AS
SELECT 
    p.id AS property_id,
    p.name AS property_name,
    p.code AS property_code,
    EXTRACT(YEAR FROM expense_date) AS year,
    EXTRACT(MONTH FROM expense_date) AS month,
    e.category,
    SUM(e.amount) AS total_amount,
    COUNT(e.id) AS expense_count
FROM 
    properties p
    LEFT JOIN expenses e ON p.id = e.property_id
GROUP BY 
    p.id, p.name, p.code, year, month, e.category;

-- Crear función para calcular morosidad
CREATE OR REPLACE FUNCTION calculate_late_fees(unit_id INTEGER, reference_date DATE)
RETURNS DECIMAL AS $$
DECLARE
    monthly_fee DECIMAL;
    last_payment_date DATE;
    months_late INTEGER;
    late_fee_rate DECIMAL := 0.10; -- 10% por mes de atraso
    total_late_fee DECIMAL := 0;
BEGIN
    -- Obtener cuota mensual
    SELECT monthly_fee INTO monthly_fee FROM units WHERE id = unit_id;
    
    -- Obtener fecha del último pago
    SELECT MAX(payment_date) INTO last_payment_date 
    FROM payments 
    WHERE unit_id = unit_id AND payment_type = 'maintenance' AND status = 'paid';
    
    -- Si no hay pagos previos, no hay mora
    IF last_payment_date IS NULL THEN
        RETURN 0;
    END IF;
    
    -- Calcular meses de atraso
    months_late := EXTRACT(YEAR FROM reference_date) * 12 + EXTRACT(MONTH FROM reference_date) - 
                  (EXTRACT(YEAR FROM last_payment_date) * 12 + EXTRACT(MONTH FROM last_payment_date));
    
    -- Si está al día o adelantado, no hay mora
    IF months_late <= 0 THEN
        RETURN 0;
    END IF;
    
    -- Calcular monto de la mora
    total_late_fee := monthly_fee * months_late * late_fee_rate;
    
    RETURN total_late_fee;
END;
$$ LANGUAGE plpgsql;

-- Mensaje de finalización
DO $$
BEGIN
    RAISE NOTICE 'Base de datos PH Control inicializada correctamente';
END $$;