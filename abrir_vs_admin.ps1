# Script para gestionar los contenedores Docker de PH Control en Windows

# Función para verificar si Docker está en ejecución
function Test-Docker {
    try {
        docker info | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

# Función para mostrar el menú
function Show-Menu {
    Clear-Host
    Write-Host "================ PH Control ================" -ForegroundColor Cyan
    Write-Host "1. Iniciar contenedores"
    Write-Host "2. Detener contenedores"
    Write-Host "3. Reiniciar contenedores"
    Write-Host "4. Ver logs"
    Write-Host "5. Estado de contenedores"
    Write-Host "6. Reconstruir contenedores"
    Write-Host "7. Abrir aplicación en navegador"
    Write-Host "8. Crear respaldo de base de datos"
    Write-Host "Q. Salir"
    Write-Host "=========================================" -ForegroundColor Cyan
}

# Verificar si Docker está en ejecución
if (-not (Test-Docker)) {
    Write-Host "❌ Docker no está en ejecución. Por favor, inicia Docker Desktop." -ForegroundColor Red
    Write-Host "Presiona cualquier tecla para salir..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    Exit
}

# Bucle principal
do {
    Show-Menu
    $input = Read-Host "Selecciona una opción"
    
    switch ($input) {
        '1' {
            Write-Host "🚀 Iniciando contenedores..." -ForegroundColor Cyan
            docker-compose up -d
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Contenedores iniciados correctamente" -ForegroundColor Green
            }
            else {
                Write-Host "❌ Error al iniciar contenedores" -ForegroundColor Red
            }
        }
        '2' {
            Write-Host "⏹️ Deteniendo contenedores..." -ForegroundColor Cyan
            docker-compose down
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Contenedores detenidos correctamente" -ForegroundColor Green
            }
            else {
                Write-Host "❌ Error al detener contenedores" -ForegroundColor Red
            }
        }
        '3' {
            Write-Host "🔄 Reiniciando contenedores..." -ForegroundColor Cyan
            docker-compose restart
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Contenedores reiniciados correctamente" -ForegroundColor Green
            }
            else {
                Write-Host "❌ Error al reiniciar contenedores" -ForegroundColor Red
            }
        }
        '4' {
            Write-Host "📋 Mostrando logs (Ctrl+C para salir)..." -ForegroundColor Cyan
            docker-compose logs -f
        }
        '5' {
            Write-Host "📊 Estado de contenedores:" -ForegroundColor Cyan
            docker-compose ps
        }
        '6' {
            Write-Host "🔨 Reconstruyendo contenedores..." -ForegroundColor Cyan
            docker-compose down
            docker-compose build
            docker-compose up -d
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Contenedores reconstruidos correctamente" -ForegroundColor Green
            }
            else {
                Write-Host "❌ Error al reconstruir contenedores" -ForegroundColor Red
            }
        }
        '7' {
            Write-Host "🌐 Abriendo aplicación en navegador..." -ForegroundColor Cyan
            Start-Process "http://localhost:5003"
        }
        '8' {
            $backupFile = "backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').sql"
            Write-Host "💾 Creando respaldo de base de datos: $backupFile" -ForegroundColor Cyan
            docker exec ph-control-database pg_dump -U phcontrol phcontrol_db > $backupFile
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Respaldo creado correctamente: $backupFile" -ForegroundColor Green
            }
            else {
                Write-Host "❌ Error al crear respaldo" -ForegroundColor Red
            }
        }
        'q' {
            return
        }
    }
    
    if ($input -ne 'q') {
        Write-Host "Presiona cualquier tecla para continuar..."
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    }
} until ($input -eq 'q')