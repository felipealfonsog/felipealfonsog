// generate-charts.js
// Genera un SVG simple con barras de ejemplo para languages-chart.svg

const fs = require("fs");

const languages = [
  { name: "Python", value: 40 },
  { name: "JavaScript", value: 30 },
  { name: "TypeScript", value: 15 },
  { name: "C", value: 10 },
  { name: "Others", value: 5 },
];

const width = 600;
const barHeight = 24;
const barGap = 12;
const leftPadding = 120;
const rightPadding = 40;
const topPadding = 40;
const bottomPadding = 40;

const maxValue = Math.max(...languages.map(l => l.value));
const innerWidth = width - leftPadding - rightPadding;
const height =
  topPadding + bottomPadding + languages.length * (barHeight + barGap);

let svg = `
<svg width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" xmlns="http://www.w3.org/2000/svg">
  <style>
    .title {
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 16px;
      font-weight: 600;
      fill: #111;
    }
    .label {
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 12px;
      fill: #111;
    }
    .value {
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 11px;
      fill: #111;
    }
    .bar-bg {
      fill: #f2f2f2;
    }
    .bar {
      fill: #222;
    }
  </style>

  <text x="${width / 2}" y="${topPadding - 12}" text-anchor="middle" class="title">
    Language usage (demo)
  </text>
`;

// barras
languages.forEach((lang, index) => {
  const y =
    topPadding + index * (barHeight + barGap);
  const barWidth = (lang.value / maxValue) * innerWidth;

  svg += `
  <text x="${leftPadding - 10}" y="${y + barHeight * 0.7}" text-anchor="end" class="label">
    ${lang.name}
  </text>

  <rect
    class="bar-bg"
    x="${leftPadding}"
    y="${y}"
    width="${innerWidth}"
    height="${barHeight}"
    rx="4"
    ry="4"
  />

  <rect
    class="bar"
    x="${leftPadding}"
    y="${y}"
    width="${barWidth}"
    height="${barHeight}"
    rx="4"
    ry="4"
  />

  <text
    x="${leftPadding + barWidth + 6}"
    y="${y + barHeight * 0.7}"
    class="value"
  >
    ${lang.value}%
  </text>
  `;
});

svg += `</svg>\n`;

fs.writeFileSync("languages-chart.svg", svg, "utf8");
console.log("languages-chart.svg generated");
