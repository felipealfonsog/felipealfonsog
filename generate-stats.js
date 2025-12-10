const fs = require("fs");
const fetch = require("node-fetch");

// ------------ GraphQL Query ----------------
const query = `
{
  viewer {
    name
    repositories(first: 100, privacy: PUBLIC, isFork: false) {
      nodes {
        name
        stargazerCount
        issues {
          totalCount
        }
        pullRequests {
          totalCount
        }
        defaultBranchRef {
          target {
            ... on Commit {
              history {
                totalCount
              }
            }
          }
        }
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges {
            size
            node {
              name
            }
          }
        }
      }
    }
  }
}
`;

async function getStats() {
  const res = await fetch("https://api.github.com/graphql", {
    method: "POST",
    headers: {
      Authorization: "Bearer " + process.env.GH_TOKEN,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ query }),
  });

  const json = await res.json();

  if (!json.data) {
    console.error(json);
    process.exit(1);
  }

  return json.data.viewer;
}

function generateMarkdown(stats) {
  let totalStars = 0;
  let totalIssues = 0;
  let totalPRs = 0;
  let totalCommits = 0;

  const langMap = {};

  stats.repositories.nodes.forEach((repo) => {
    totalStars += repo.stargazerCount;
    totalIssues += repo.issues.totalCount;
    totalPRs += repo.pullRequests.totalCount;
    totalCommits += repo.defaultBranchRef?.target?.history?.totalCount || 0;

    repo.languages.edges.forEach((edge) => {
      const name = edge.node.name;
      langMap[name] = (langMap[name] || 0) + edge.size;
    });
  });

  const languagesRanked = Object.entries(langMap)
    .sort((a, b) => b[1] - a[1])
    .map(([name, size]) => `- **${name}**: ${size} bytes`)
    .join("\n");

  return `
## 📊 GitHub Stats (Auto-updated)

**Total Stars:** ${totalStars}  
**Total Issues:** ${totalIssues}  
**Total PRs:** ${totalPRs}  
**Total Commits:** ${totalCommits}  

### 🔥 Languages Used (by code size)
${languagesRanked}

---
*(Auto-generated via GitHub Actions — no external services)*
`;
}

async function run() {
  const stats = await getStats();
  const md = generateMarkdown(stats);

  let readme = fs.readFileSync("README.md", "utf8");

  const start = "<!--STATS-START-->";
  const end = "<!--STATS-END-->";

  const block = `${start}\n${md}\n${end}`;

  if (readme.includes(start)) {
    readme = readme.replace(
      new RegExp(`${start}[\\s\\S]*?${end}`),
      block
    );
  } else {
    readme += `\n${block}\n`;
  }

  fs.writeFileSync("README.md", readme);
}

run();
