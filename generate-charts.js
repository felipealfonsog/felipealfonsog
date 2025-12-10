import fs from "fs";
import fetch from "node-fetch";

async function getLanguages() {
  const res = await fetch("https://api.github.com/users/felipealfonsog/repos?per_page=100", {
    headers: { "User-Agent": "chart-generator" }
  });

  const repos = await res.json();

  const totals = {};

  for (const repo of repos) {
    const langRes = await fetch(repo.languages_url, {
      headers: { "User-Agent": "chart-generator" }
    });

    const data = await langRes.json();

    for (const [lang, bytes] of Object.entries(data)) {
      totals[lang] = (totals[lang] || 0) + bytes;
    }
  }

  return totals;
}

function generateSVG(data) {
  const totalBytes = Object.values(data).reduce((a, b) => a + b, 0);

  let bars = "";
  let y = 20;

  for (const [lang, bytes] of Object.entries(data)) {
    const percent = ((bytes / totalBytes) * 100).toFixed(1);

    bars += `
      <div class="bar" style="--value:${percent}%">
        <span>${lang} — ${percent}%</span>
      </div>
    `;
    y += 25;
  }

  return `
  <svg xmlns="http://www.w3.org/2000/svg" width="600" height="${y + 20}">
    <foreignObject width="100%" height="100%">
      <div xmlns="http://www.w3.org/1999/xhtml">
        <style>
          .bar { 
            height: 20px;
            margin-bottom: 6px;
            background: #e0e0e0;
            position: relative;
          }
          .bar::before {
            content: '';
            position: absolute;
            top: 0; left:0;
            height: 100%;
            width: var(--value);
            background: #444;
          }
        </style>
        ${bars}
      </div>
    </foreignObject>
  </svg>
  `;
}

async function main() {
  const data = await getLanguages();
  const svg = generateSVG(data);

  fs.writeFileSync("languages-chart.svg", svg);
  console.log("languages-chart.svg generated!");
}

main();
