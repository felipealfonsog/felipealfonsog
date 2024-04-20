import requests

def generate_readme_and_listrepos(num_repos):
    try:
        # Make a request to the GitHub API to get the user's most recent repositories
        response = requests.get(f"https://api.github.com/users/felipealfonsog/repos?sort=updated&per_page={num_repos}")

        if not response.ok:
            raise Exception(f"Error fetching repositories: {response.status_code} - {response.reason}")

        repos = response.json()

        # Sort the repositories by the last updated date (from most recent to oldest)
        sorted_repos = sorted(repos, key=lambda x: x['updated_at'], reverse=True)

        # Build the content for the list of repositories
        repos_content = " \n"
        for repo in sorted_repos:
            repos_content += f"- [{repo['full_name']}]({repo['html_url']})\n"

        # Read the content of the README.md file
        with open('README.md', 'r') as file:
            readme_content = file.read()

        # Find the start and end markers for the repositories section
        start_marker = '<!-- START_SECTION:repos -->'
        end_marker = '<!-- END_SECTION:repos -->'

        # Find the start and end indices of the repositories section
        start_index = readme_content.find(start_marker)
        end_index = readme_content.find(end_marker)

        if start_index == -1 or end_index == -1:
            raise Exception("Markers not found in README.md")

        # Extract the content between the markers
        existing_content = readme_content[start_index + len(start_marker):end_index]

        # Replace the existing content with the new repositories content
        new_readme_content = readme_content.replace(existing_content, repos_content)

        # Save the new content to the README.md file
        with open('README.md', 'w') as file:
            file.write(new_readme_content)

        print("README.md updated successfully!")

        # Update the content of the listrepos.md file
        with open('listrepos.md', 'w') as file:
            file.write(repos_content)

        print("listrepos.md updated successfully!")

        # Update the content of the LISTINGREPOS.md file
        with open('LISTINGREPOS.md', 'w') as file:
            file.write(repos_content)

        print("LISTINGREPOS.md updated successfully!")
    except Exception as e: 
        print(f"Error generating files: {e}")

# Call the function to update README.md with the list of repositories
generate_readme_and_listrepos(13)
