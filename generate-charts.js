const { ChartJSNodeCanvas } = require('chartjs-node-canvas');
const fs = require('fs');
const fetch = require('node-fetch');

const width = 800;
const height = 600;

async function getLanguages() {
    const res = await fetch('https://api.github.com/users/felipealfonsog/repos');
    const repos = await res.json();

    const languageCount = {};

    for (const repo of repos) {
        if (repo.language) {
            languageCount[repo.language] = (languageCount[repo.language] || 0) + 1;
        }
    }

    return languageCount;
}

async function createChart() {
    const languages = await getLanguages();
    const labels = Object.keys(languages);
    const values = Object.values(languages);

    const chart = new ChartJSNodeCanvas({ width, height });

    const configuration = {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'Most used languages',
                data: values,
            }],
        },
    };

    const image = await chart.renderToBuffer(configuration);
    fs.writeFileSync('languages-chart.svg', image);
}

createChart();
