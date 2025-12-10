import fs from "fs";
import fetch from "node-fetch";

const TOKEN = process.env.GH_STATS_TOKEN;

async function fetchStats() {
    const query = `
      query {
        viewer {
          login
          repositories(first: 100, ownerAffiliations: OWNER, orderBy: {field: UPDATED_AT, direction: DESC}) {
            nodes {
              name
              stargazerCount
              languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
                edges {
                  size
                  node {
                    name
                    color
                  }
                }
              }
            }
          }
        }
      }
    `;

    const response = await fetch("https://api.github.com/graphql", {
        method: "POST",
        headers: {
            "Authorization": `Bearer ${TOKEN}`,
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ query })
    });

    const json = await response.json();

    if (!json.data) {
        console.error("ERROR: ", json);
        process.exit(1);
    }

    return json.data.viewer.repositories.nodes;
}

function generateSVG(data) {
    let totalStars = 0;
    const languageUsage = {};

    data.forEach(repo => {
        totalStars += repo.stargazerCount;

        repo.languages.edges.forEach(lang => {
            if (!languageUsage[lang.node.name]) languageUsage[lang.node.name] = 0;
            languageUsage[lang.node.name] += lang.size;
        });
    });

    const sortedLangs = Object.entries(languageUsage)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 6);

    let bars = "";
    sortedLangs.forEach(([name, size]) => {
        bars += `
        <div class="bar">
          <span>${name}</span>
          <div class="value" style="width:${size / 1000}px"></div>
        </div>`;
    });

    const svg = `
      <svg xmlns="http://www.w3.org/2000/svg" width="450" height="240">
        <style>
          .bar { font-family: sans-serif; font-size: 13px; margin: 4px 0; }
          .value { height: 8px; background: #ff0033; }
          text { font-family: monospace; }
        </style>
        <text x="10" y="20">Total Stars: ${totalStars}</text>
        <text x="10" y="40">Top Languages:</text>
        <foreignObject x="10" y="50" width="430" height="200">
          <div xmlns="http://www.w3.org/1999/xhtml">
            ${bars}
          </div>
        </foreignObject>
      </svg>
    `;

    fs.writeFileSync("stats.svg", svg);
}

(async () => {
    const data = await fetchStats();
    generateSVG(data);
})();
