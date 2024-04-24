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

        # Read the content of the LISTINGREPOS.md file
        with open('LISTINGREPOS.md', 'r') as file:
            listrepos_content = file.read()

        # Check if there are any changes in the generated content
        if repos_content != listrepos_content or repos_content not in readme_content:
            # Replace the content in README.md
            with open('README.md', 'w') as file:
                file.write(repos_content)
            print("README.md updated successfully!")

            # Replace the content in LISTINGREPOS.md
            with open('LISTINGREPOS.md', 'w') as file:
                file.write(repos_content)
            print("LISTINGREPOS.md updated successfully!")
        else:
            print("No changes detected, skipping update.")
    except Exception as e:
        print(f"Error generating files: {e}")

# Call the function to update README.md and LISTINGREPOS.md with the list of repositories
generate_readme_and_listrepos(13)
