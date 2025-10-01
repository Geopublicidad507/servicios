import requests
import json
from flask import current_app
from typing import Dict, Any, Optional

class APIClient:
    def __init__(self):
        self.base_url = None
        self.timeout = 30
        self.session = requests.Session()
    
    def init_app(self, app):
        self.base_url = app.config.get('API_BASE_URL')
        self.timeout = app.config.get('API_TIMEOUT', 30)
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                     params: Optional[Dict] = None) -> Dict[str, Any]:
        """Realizar petición HTTP a la API"""
        try:
            url = f"{self.base_url}/{endpoint.lstrip('/')}"
            
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=headers,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            return response.json() if response.content else {}
            
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"API request failed: {e}")
            return {'error': str(e), 'success': False}
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        return self._make_request('GET', endpoint, params=params)
    
    def post(self, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        return self._make_request('POST', endpoint, data=data)
    
    def put(self, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        return self._make_request('PUT', endpoint, data=data)
    
    def delete(self, endpoint: str) -> Dict[str, Any]:
        return self._make_request('DELETE', endpoint)

# Instancia global
api_client = APIClient()