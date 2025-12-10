const axios = require("axios");
const fs = require("fs");

const query = `
{
  viewer {
    name
    repositories(first: 100, privacy: PUBLIC) {
      totalCount
      nodes {
        stargazerCount
        name
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          nodes {
            name
          }
        }
      }
    }
  }
}
`;

(async () => {
  try {
    const res = await axios.post(
      "https://api.github.com/graphql",
      { query },
      {
        headers: {
          Authorization: `bearer ${process.env.GH_TOKEN}`,
        },
      }
    );

    const data = res.data.data.viewer;

    let totalStars = 0;
    let languageCount = {};

    for (const repo of data.repositories.nodes) {
      totalStars += repo.stargazerCount;

      for (const lang of repo.languages.nodes) {
        languageCount[lang.name] = (languageCount[lang.name] || 0) + 1;
      }
    }

    const topLanguages = Object.entries(languageCount)
      .sort((a, b) => b[1] - a[1])
      .map(([lang, count]) => `- ${lang} (${count})`)
      .join("\n");

    const output = `
# 🔧 GitHub Stats (Auto-Generated)

**Total Stars:** ${totalStars}

**Top Languages:**
${topLanguages}

(Updated automatically every 24 hours)
`;

    fs.writeFileSync("README_STATS.md", output);
  } catch (error) {
    console.error(error);
    process.exit(1);
  }
})();
