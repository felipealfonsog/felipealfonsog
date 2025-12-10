import fs from "fs";
import fetch from "node-fetch";

// Configura tu usuario
const username = "felipealfonsog";

async function fetchLanguages() {
  const res = await fetch(`https://api.github.com/users/${username}/repos`);
  const repos = await res.json();

  const totals = {};

  for (const repo of repos) {
    const langRes = await fetch(repo.languages_url);
    const langs = await langRes.json();

    for (const [lang, bytes] of Object.entries(langs)) {
      totals[lang] = (totals[lang] || 0) + bytes;
    }
  }
  return totals;
}

function generateSVG(data) {
  const total = Object.values(data).reduce((a, b) => a + b, 0);
  const entries = Object.entries(data)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10);

  // Chart.css estilo barras horizontales
  const rows = entries
    .map(([lang, bytes]) => {
      const pct = ((bytes / total) * 100).toFixed(2);
      return `
        <tr>
          <th>${lang}</th>
          <td style="--size:${pct / 100}">${pct}%</td>
        </tr>
      `;
    })
    .join("");

  return `
<svg xmlns="http://www.w3.org/2000/svg" width="600" height="${entries.length * 30}">
  <foreignObject width="600" height="${entries.length * 30}">
    <body xmlns="http://www.w3.org/1999/xhtml">
      <link rel="stylesheet" href="https://unpkg.com/charts.css/dist/charts.min.css" />
      <table class="charts-css bar show-labels show-primary-axis show-data-axes">
        <tbody>
          ${rows}
        </tbody>
      </table>
    </body>
  </foreignObject>
</svg>
`;
}

async function main() {
  const data = await fetchLanguages();
  const svg = generateSVG(data);
  fs.writeFileSync("languages-chart.svg", svg);
}

main();
