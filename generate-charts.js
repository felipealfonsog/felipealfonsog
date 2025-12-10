const { Octokit } = require("@octokit/rest");
const { ChartJSNodeCanvas } = require("chartjs-node-canvas");
const fs = require("fs");

const octokit = new Octokit({
  auth: process.env.GITHUB_TOKEN,
});

const USERNAME = "felipealfonsog";

async function getLanguages() {
  const repos = await octokit.repos.listForUser({
    username: USERNAME,
    per_page: 100,
  });

  const totals = {};

  for (const repo of repos.data) {
    const langs = await octokit.repos.listLanguages({
      owner: USERNAME,
      repo: repo.name,
    });

    for (const [lang, bytes] of Object.entries(langs.data)) {
      totals[lang] = (totals[lang] || 0) + bytes;
    }
  }

  return totals;
}

async function generateChart() {
  const data = await getLanguages();

  const labels = Object.keys(data);
  const values = Object.values(data);

  const width = 800;
  const height = 400;
  const chart = new ChartJSNodeCanvas({ width, height });

  const buffer = await chart.renderToBuffer({
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: "Languages by bytes",
          data: values,
        },
      ],
    },
  });

  fs.writeFileSync("languages-chart.svg", buffer);
}

generateChart();
