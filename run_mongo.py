#!/usr/bin/env python3
"""
Script de ejecución para PH Control con MongoDB Cloud
"""
import os
import sys
from app import app

if __name__ == "__main__":
    print("🚀 Iniciando PH Control con MongoDB Cloud...")
    print("🌐 API Base: https://printed-binny-consultor351-faafa5db.koyeb.app")
    print("📦 MongoDB: consultor351.yv7gbsp.mongodb.net")
    
    port = int(os.environ.get('PORT', 5003))
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    print(f"🚀 Puerto: {port}")
    print(f"🐛 Debug: {debug}")
    print("=" * 50)
    
    app.run(debug=debug, host='0.0.0.0', port=port)