"""Deploy - generates docker-compose.yml for deployment"""

from typing import Dict, Any
import os


class DeployAgent:
    """Generate deployment configurations (docker-compose.yml)"""

    def __init__(self):
        pass

    def generate_deployment(self, bindings_data: Dict[str, Any], output_dir: str) -> str:
        """Generate docker-compose.yml based on bindings"""

        # Group placements by layer
        layers = {'cloud': [], 'edge': [], 'device': []}

        for placement in bindings_data.get('placements', []):
            layer = placement.get('layer', 'cloud')
            if layer in layers:
                layers[layer].append(placement)

        # Generate docker-compose content
        compose_content = self._generate_docker_compose(layers, bindings_data)

        # Save docker-compose.yml
        compose_file = os.path.join(output_dir, 'docker-compose.yml')
        with open(compose_file, 'w', encoding='utf-8') as f:
            f.write(compose_content)

        return compose_file

    def _generate_docker_compose(self, layers: Dict[str, list], bindings_data: Dict[str, Any]) -> str:
        """Generate docker-compose.yml content"""

        content = """version: '3.8'

services:
"""

        # Generate service for each layer
        for layer, placements in layers.items():
            if placements:
                content += f"""
  {layer}_service:
    build:
      context: ./generated_code/{layer}
      dockerfile: Dockerfile
    container_name: autopipeline_{layer}
    environment:
      - LAYER={layer.upper()}
      - SERVICE_NAME={layer}_service
    volumes:
      - ./generated_code/{layer}:/app
    # TODO: Add port mappings based on endpoints
    # ports:
    #   - "8080:8080"
    networks:
      - autopipeline_network
    restart: unless-stopped
"""

        # Add network definition
        content += """
networks:
  autopipeline_network:
    driver: bridge

# TODO: Add volumes if needed for persistent storage
# volumes:
#   data_volume:
"""

        # Add comments about transports
        content += "\n# Transport protocols used:\n"
        for transport in bindings_data.get('transports', []):
            content += f"# - {transport['link_id']}: {transport['protocol']} (QoS: {transport.get('qos', 'N/A')})\n"

        return content
