import requests

def generate_readme_and_listrepos(num_repos):
    try:
        # Make a request to the GitHub API to get the user's most recent repositories
        response = requests.get(f"https://api.github.com/users/felipealfonsog/repos?sort=updated&per_page={num_repos}")

        if not response.ok:
            raise Exception(f"Error fetching repositories: {response.status_code} - {response.reason}")

        repos = response.json()

        # Build the content for the list of repositories
        repos_content = f"## Last {num_repos} Repositories\n\n"
        for repo in repos:
            repos_content += f"- [{repo['full_name']}]({repo['html_url']})\n"

        # Read the content of the README.md file
        with open('README.md', 'r') as file:
            readme_content = file.read()

        # Replace the repositories section in the README with the dynamic content
        new_readme_content = readme_content.replace('<!-- START_SECTION:repos -->\n<!-- Here dynamically insert the list of repositories -->\n<!-- END_SECTION:repos -->', repos_content)

        # Save the new content to the README.md file
        with open('README.md', 'w') as file:
            file.write(new_readme_content)

        print("README.md generated successfully!")

        # Write the repositories content to the listrepos.md file
        with open('listrepos.md', 'w') as file:
            file.write(repos_content)

        print("listrepos.md generated successfully!")
    except Exception as e:
        print(f"Error generating files: {e}")

# Call the function to generate both README.md and listrepos.md with the list of repositories
generate_readme_and_listrepos(20)
