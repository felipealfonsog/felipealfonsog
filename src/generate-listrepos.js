const fs = require('fs');
const fetch = require('node-fetch');

async function generateListRepos(numRepos) {
    try {
        // Obtiene los repositorios más recientes del usuario felipealfonsog
        const response = await fetch(`https://api.github.com/users/felipealfonsog/repos?sort=updated&per_page=${numRepos}`);

        if (!response.ok) {
            throw new Error(`Error al obtener repositorios: ${response.status} - ${response.statusText}`);
        }

        const repos = await response.json();

        // Construye el contenido del archivo listrepos.md
        let content = `## Últimos ${numRepos} Repositorios\n\n`;
        repos.forEach(repo => {
            content += `- [${repo.full_name}](${repo.html_url})\n`;
        });

        // Escribe el contenido en el archivo listrepos.md
        fs.writeFileSync('listrepos.md', content);

        console.log('Archivo listrepos.md generado correctamente.');
    } catch (error) {
        console.error('Error al generar el archivo listrepos.md:', error.message);
    }
}

generateListRepos(process.argv[2]);
