import requests

def generate_list_repos(num_repos):
    try:
        # Hace una solicitud a la API de GitHub para obtener los repositorios más recientes del usuario felipealfonsog
        response = requests.get(f"https://api.github.com/users/felipealfonsog/repos?sort=updated&per_page={num_repos}")

        if not response.ok:
            raise Exception(f"Error fetching repositories: {response.status_code} - {response.reason}")

        repos = response.json()

        # Construye el contenido del archivo listrepos.md
        content = f"## Last {num_repos} Repositories\n\n"
        for repo in repos:
            content += f"- [{repo['full_name']}]({repo['html_url']})\n"

        # Escribe el contenido en el archivo listrepos.md
        with open('listrepos.md', 'w') as file:
            file.write(content)

        print("listrepos.md generated successfully!")
    except Exception as e:
        print(f"Error generating listrepos.md: {e}")

# Llama a la función para generar listrepos.md con el número de repositorios especificado
generate_list_repos(15)
