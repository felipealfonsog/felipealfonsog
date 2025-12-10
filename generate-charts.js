const fs = require("fs");

// Datos falsos de ejemplo — después los reemplazamos por API real si quieres
const data = [
  { language: "JavaScript", percent: 40 },
  { language: "Python", percent: 25 },
  { language: "C", percent: 15 },
  { language: "Go", percent: 10 },
  { language: "Other", percent: 10 }
];

// Generar SVG con estilo limpio
let bars = "";
let y = 20;

data.forEach(item => {
  bars += `
    <text x="10" y="${y}" font-size="12" font-family="monospace">${item.language}</text>
    <rect x="120" y="${y - 10}" width="${item.percent * 3}" height="12" fill="black" />
    <text x="${130 + item.percent * 3}" y="${y}" font-size="12" font-family="monospace">${item.percent}%</text>
  `;
  y += 25;
});

const svg = `
<svg width="600" height="${data.length * 30}" xmlns="http://www.w3.org/2000/svg">
  <style>
    text { fill: #000; }
  </style>
  ${bars}
</svg>
`;

fs.writeFileSync("languages-chart.svg", svg);
console.log("languages-chart.svg generado.");
