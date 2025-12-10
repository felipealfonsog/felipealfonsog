// generate-charts.js
// Analiza lenguajes de tus repos y genera un SVG usando Charts.css

const { execSync } = require("child_process");
const fs = require("fs");

// 1. Obtiene datos de GitHub mediante la API CLI
function getLanguages() {
  const output = execSync(
    "gh api /users/felipealfonsog/repos --paginate --jq '.[].language'"
  )
    .toString()
    .trim()
    .split("\n")
    .filter(Boolean);

  const counts = {};
  for (const lang of output) {
    counts[lang] = (counts[lang] || 0) + 1;
  }
  return counts;
}

const languages = getLanguages();

// 2. Convierte datos a barras SVG usando Charts.css
const bars = Object.entries(languages)
  .map(([lang, count]) => {
    return `
      <tr>
        <th>${lang}</th>
        <td style="--size:${count / 10}">
          ${count}
        </td>
      </tr>
    `;
  })
  .join("\n");

// 3. Genera el SVG final
const svg = `
<svg xmlns="http://www.w3.org/2000/svg" width="600" height="${
  40 + Object.keys(languages).length * 30
}">
  <foreignObject width="100%" height="100%">
    <style>
      @import "https://cdn.jsdelivr.net/npm/charts.css/dist/charts.min.css";
      table {
        font-family: monospace;
        font-size: 14px;
        width: 100%;
      }
      td {
        background: #0af;
      }
    </style>

    <table class="charts-css bar show-labels">
      <tbody>
        ${bars}
      </tbody>
    </table>
  </foreignObject>
</svg>
`;

fs.writeFileSync("languages-chart.svg", svg);
console.log("languages-chart.svg generado correctamente.");
