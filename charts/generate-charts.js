const { graphql } = require("@octokit/graphql");
const fs = require("fs");

(async () => {
  const token = process.env.GITHUB_TOKEN;

  if (!token) {
    console.error("Missing GITHUB_TOKEN");
    process.exit(1);
  }

  const client = graphql.defaults({
    headers: {
      authorization: `token ${token}`,
    },
  });

  // Query GH API for languages used in repos
  const query = `
    query UsedLanguages($login: String!) {
      user(login: $login) {
        repositories(first: 100, isFork: false, ownerAffiliations: OWNER) {
          nodes {
            name
            languages(first: 10) {
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

  const data = await client(query, { login: "felipealfonsog" });

  // Aggregate language sizes
  const langTotals = {};

  data.user.repositories.nodes.forEach(repo => {
    repo.languages.edges.forEach(edge => {
      const name = edge.node.name;
      const size = edge.size;

      if (!langTotals[name]) langTotals[name] = 0;
      langTotals[name] += size;
    });
  });

  const total = Object.values(langTotals).reduce((a, b) => a + b, 0);

  // Transform to percentage
  const processed = Object.entries(langTotals)
    .map(([name, size]) => ({
      name,
      percent: ((size / total) * 100).toFixed(2),
    }))
    .sort((a, b) => b.percent - a.percent);

  // Build SVG with Charts.css
  const bars = processed
    .map(
      (lang) => `
      <tr>
        <th>${lang.name}</th>
        <td style="--size: ${lang.percent / 100}">
          ${lang.percent}%
        </td>
      </tr>`
    )
    .join("");

  const svg = `
  <svg xmlns="http://www.w3.org/2000/svg" width="600" height="${
    40 + processed.length * 30
  }">
    <foreignObject width="100%" height="100%">
      <style>
        table {
          font-family: monospace;
          width: 100%;
        }
        td {
          --color: #4caf50;
        }
        [role="bar"] {
          background: var(--color);
          height: 20px;
        }
      </style>

      <div xmlns="http://www.w3.org/1999/xhtml">
        <h3>Language Usage (Auto-Generated)</h3>
        <table>
          ${bars}
        </table>
      </div>
    </foreignObject>
  </svg>
  `;

  fs.writeFileSync("languages-chart.svg", svg.trim());
  console.log("languages-chart.svg generated.");
})();
