import fetch from 'node-fetch';

async function generateListRepos(numRepos) {
    try {
        // Get the most recent repositories of the user felipealfonsog
        const response = await fetch(`https://api.github.com/users/felipealfonsog/repos?sort=updated&per_page=${numRepos}`);

        if (!response.ok) {
            throw new Error(`Error fetching repositories: ${response.status} - ${response.statusText}`);
        }

        const repos = await response.json();

        // Construct the content of the listrepos.md file
        let content = `## Last ${numRepos} Repositories\n\n`;
        repos.forEach(repo => {
            content += `- [${repo.full_name}](${repo.html_url})\n`;
        });

        // Print the content to console
        console.log(content);
    } catch (error) {
        console.error('Error generating listrepos.md:', error.message);
    }
}

const NUM_REPOS = process.argv[2];
generateListRepos(NUM_REPOS);
