import requests
from bs4 import BeautifulSoup
import feedgenerator
from datetime import datetime, timedelta
import hashlib
import json
import os

class MuseoReinaSofiaFeedGenerator:
    def __init__(self):
        self.base_url = "https://www.museoreinasofia.es/exposiciones"
        self.feed_file = "exposiciones-reina-sofia.xml"
        self.cache_file = "feed_cache.json"
        self.feed_url = "https://feeds.brunovegadeseoane.com/exposiciones-reina-sofia.xml"
        
    def fetch_exposiciones(self):
        """Extrae las exposiciones temporales de la web del museo"""
        print("🔍 Conectando con el Museo Reina Sofía...")
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(self.base_url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            exposiciones = []
            
            # Buscar todas las tarjetas de exposiciones
            # Estos selectores pueden necesitar ajustes
            cards = soup.find_all('div', class_=lambda x: x and any(word in x.lower() for word in ['card', 'item', 'expo', 'grid', 'col']))
            
            if not cards:
                # Fallback: buscar cualquier contenedor que pueda tener exposiciones
                cards = soup.find_all(['article', 'div', 'section'])[:20]
            
            for card in cards[:12]:  # Limitar a 12 exposiciones
                exposicion = self._parse_exposicion(card)
                if exposicion and self._is_valid_exposicion(exposicion):
                    exposiciones.append(exposicion)
            
            print(f"✅ Encontradas {len(exposiciones)} exposiciones")
            return exposiciones
            
        except Exception as e:
            print(f"❌ Error al obtener datos: {e}")
            return self._get_fallback_data()
    
    def _parse_exposicion(self, container):
        """Parsea un contenedor individual de exposición"""
        try:
            # Extraer título
            title_elem = (container.find(['h1', 'h2', 'h3', 'h4']) or 
                         container.find('a') or 
                         container.find('strong'))
            title = title_elem.get_text(strip=True) if title_elem else "Exposición Temporal"
            
            # Limpiar título
            if len(title) > 100:
                title = title[:100] + "..."
            
            # Extraer descripción
            desc_elem = container.find(['p', 'span', 'div'])
            description = desc_elem.get_text(strip=True)[:200] if desc_elem else "Exposición temporal en el Museo Reina Sofía"
            
            # Extraer enlace
            link_elem = container.find('a', href=True)
            if link_elem:
                link = link_elem['href']
                if link.startswith('/'):
                    link = f"https://www.museoreinasofia.es{link}"
            else:
                link = self.base_url
            
            # Buscar fechas en el texto
            date_text = ""
            text_content = container.get_text()
            date_keywords = ['hasta', 'del', 'desde', '2024', '2025', 'enero', 'febrero', 'marzo']
            if any(keyword in text_content.lower() for keyword in date_keywords):
                date_text = text_content[:100]
            
            # Generar ID único
            item_id = hashlib.md5(f"{title}{description}".encode()).hexdigest()
            
            return {
                'id': item_id,
                'title': title,
                'link': link,
                'description': description,
                'date_text': date_text,
                'pub_date': datetime.now()
            }
            
        except Exception as e:
            return None
    
    def _is_valid_exposicion(self, exposicion):
        """Filtra exposiciones válidas"""
        return (exposicion['title'] and 
                exposicion['title'] != 'Exposición Temporal' and
                len(exposicion['title']) > 3)
    
    def _get_fallback_data(self):
        """Datos de ejemplo si falla la conexión"""
        return [
            {
                'id': 'fallback1',
                'title': 'Exposiciones del Museo Reina Sofía',
                'link': 'https://www.museoreinasofia.es/exposiciones',
                'description': 'Consulta la web oficial para las exposiciones actuales',
                'date_text': 'Actualizado semanalmente',
                'pub_date': datetime.now()
            }
        ]
    
    def generate_rss_feed(self):
        """Genera el feed RSS con las exposiciones"""
        exposiciones = self.fetch_exposiciones()
        
        # Crear feed RSS
        feed = feedgenerator.Rss201rev2Feed(
            title="Exposiciones Temporales - Museo Reina Sofía",
            link="https://www.museoreinasofia.es/exposiciones",
            description="Feed semanal con las exposiciones temporales actuales del Museo Nacional Centro de Arte Reina Sofía",
            language="es",
            feed_url="https://feeds.brunovegadeseoane.com/exposiciones-reina-sofia.xml"

        )
        
        for expo in exposiciones:
            # Crear descripción enriquecida
            full_description = f"""
            <h3>{expo['title']}</h3>
            {f"<p><strong>Información:</strong> {expo['date_text']}</p>" if expo['date_text'] else ""}
            <p>{expo['description']}</p>
            <p><a href="{expo['link']}">Visitar exposición en web oficial</a></p>
            <hr>
            <small>Actualizado automáticamente cada semana</small>
            """
            
            feed.add_item(
                title=expo['title'],
                link=expo['link'],
                description=full_description,
                unique_id=expo['id'],
                pubdate=expo['pub_date'],
                categories=['Arte', 'Exposiciones', 'Museo Reina Sofía']
            )
        
        # Guardar feed
        with open(self.feed_file, 'w', encoding='utf-8') as f:
            feed.write(f, 'utf-8')
        
        print(f"📄 Feed RSS generado: {self.feed_file}")
        return exposiciones

def main():
    print("🚀 Iniciando generación de feed RSS...")
    generator = MuseoReinaSofiaFeedGenerator()
    exposiciones = generator.generate_rss_feed()
    print(f"🎉 Proceso completado. {len(exposiciones)} exposiciones procesadas.")

if __name__ == "__main__":
    main()