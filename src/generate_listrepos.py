import os
import requests

def generate_readme_and_listrepos(num_repos):
    try:
        # Obtener el token de acceso desde el secreto
        token = os.getenv('GH_TOKEN_LRGH_CLASS')

        if not token:
            raise Exception("GitHub token not found. Make sure to set the GH_TOKEN_LRGH_CLASS environment variable.")

        headers = {
            'Authorization': f'token {token}'
        }

        # Hacer una solicitud a la API de GitHub para obtener los repositorios más recientes del usuario
        response = requests.get(f"https://api.github.com/users/felipealfonsog/repos?sort=updated&per_page={num_repos}", headers=headers)

        if not response.ok:
            raise Exception(f"Error fetching repositories: {response.status_code} - {response.reason}")

        repos = response.json()

        # Ordenar los repositorios por la fecha de actualización (del más reciente al más antiguo)
        sorted_repos = sorted(repos, key=lambda x: x['updated_at'], reverse=True)

        # Construir el contenido para la lista de repositorios
        repos_content = ""
        for repo in sorted_repos:
            repos_content += f"- [{repo['full_name']}]({repo['html_url']})\n"

        # Leer el contenido del archivo README.md
        with open('README.md', 'r') as file:
            readme_content = file.read()

        # Encontrar los marcadores de inicio y fin para la sección de repositorios
        start_marker = '<!-- START_SECTION:repos -->'
        end_marker = '<!-- END_SECTION:repos -->'

        # Encontrar los índices de inicio y fin de la sección de repositorios
        start_index = readme_content.find(start_marker)
        end_index = readme_content.find(end_marker)

        if start_index == -1 or end_index == -1:
            raise Exception("Markers not found in README.md")

        # Extraer el contenido entre los marcadores
        existing_content = readme_content[start_index + len(start_marker):end_index]

        # Reemplazar el contenido existente con el nuevo contenido de los repositorios
        new_readme_content = readme_content.replace(existing_content, repos_content)

        # Guardar el nuevo contenido en el archivo README.md
        with open('README.md', 'w') as file:
            file.write(new_readme_content)

        print("README.md updated successfully!")

        # Actualizar el contenido del archivo LISTINGREPOS.md
        with open('LISTINGREPOS.md', 'w') as file:
            file.write(repos_content)

        print("LISTINGREPOS.md updated successfully!")
    except Exception as e: 
        print(f"Error generating files: {e}")

# Llamar a la función para actualizar README.md con la lista de repositorios
generate_readme_and_listrepos(13)
