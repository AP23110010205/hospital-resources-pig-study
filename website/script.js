
const files = {
  forecast: "../output/hospital_forecast.csv",
  beds: "../output/bed_optimization_results.csv",
  fairness: "../output/state_fairness_audit.csv",
  metrics: "../output/model_metrics.csv",
  features: "../output/feature_importance.csv",
  explanations: "../output/hospital_explanations.csv"
};

let charts = [];

function parseCSV(text) {
  const rows = [];
  let row = [];
  let field = "";
  let quoted = false;

  for (let i = 0; i < text.length; i++) {
    const char = text[i];

    if (quoted) {
      if (char === '"' && text[i + 1] === '"') {
        field += '"';
        i++;
      } else if (char === '"') {
        quoted = false;
      } else {
        field += char;
      }
    } else if (char === '"') {
      quoted = true;
    } else if (char === ",") {
      row.push(field);
      field = "";
    } else if (char === "\n") {
      row.push(field);
      rows.push(row);
      row = [];
      field = "";
    } else if (char !== "\r") {
      field += char;
    }
  }

  if (field.length || row.length) {
    row.push(field);
    rows.push(row);
  }

  const headers = rows.shift().map(h => h.trim());

  return rows
    .filter(r => r.some(value => value.trim() !== ""))
    .map(r => {
      const item = {};
      headers.forEach((header, index) => {
        item[header] = (r[index] || "").trim();
      });
      return item;
    });
}

async function loadCSV(path) {
  const response = await fetch(path);

  if (!response.ok) {
    throw new Error(`Could not load ${path}`);
  }

  return parseCSV(await response.text());
}

function number(value) {
  const result = Number(value);
  return Number.isFinite(result) ? result : 0;
}

function formatNumber(value) {
  return Math.round(number(value)).toLocaleString("en-IN");
}

function escapeHTML(value) {
  return String(value ?? "").replace(/[&<>"']/g, char => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
  })[char]);
}

function renderTable(elementId, data, limit = 10) {
  const element = document.getElementById(elementId);

  if (!element || !data.length) return;

  const columns = Object.keys(data[0]);

  element.innerHTML = `
    <table>
      <thead>
        <tr>${columns.map(col => `<th>${escapeHTML(col.replaceAll("_", " "))}</th>`).join("")}</tr>
      </thead>
      <tbody>
        ${data.slice(0, limit).map(item => `
          <tr>
            ${columns.map(col => `<td>${escapeHTML(item[col])}</td>`).join("")}
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
}

function createChart(id, config) {
  const canvas = document.getElementById(id);

  if (!canvas || typeof Chart === "undefined") return;

  const chart = new Chart(canvas, config);
  charts.push(chart);
}

function destroyCharts() {
  charts.forEach(chart => chart.destroy());
  charts = [];
}

function downloadLink(path, label) {
  return `<a href="${path}" download>${escapeHTML(label)}</a>`;
}

async function loadDashboard() {
  try {
    const [forecast, beds, fairness, metrics, features, explanations] =
      await Promise.all([
        loadCSV(files.forecast),
        loadCSV(files.beds),
        loadCSV(files.fairness),
        loadCSV(files.metrics),
        loadCSV(files.features),
        loadCSV(files.explanations)
      ]);

    const metric = metrics[0] || {};

    document.getElementById("hospitalCount").textContent =
      formatNumber(beds.length);

    document.getElementById("additionalBeds").textContent =
      formatNumber(beds.reduce((sum, item) =>
        sum + number(item.additional_beds_needed), 0));

    document.getElementById("spareBeds").textContent =
      formatNumber(beds.reduce((sum, item) =>
        sum + number(item.spare_beds), 0));

    document.getElementById("stateCount").textContent =
      formatNumber(fairness.length);

    destroyCharts();

    createChart("modelChart", {
      type: "bar",
      data: {
        labels: ["MAE", "RMSE"],
        datasets: [
          {
            label: "Random Forest",
            data: [number(metric.MAE), number(metric.RMSE)]
          },
          {
            label: "Previous-week baseline",
            data: [
              number(metric.Baseline_MAE),
              number(metric.Baseline_RMSE)
            ]
          }
        ]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: "bottom" }
        }
      }
    });

    const shortageStates = [...fairness]
      .sort((a, b) =>
        number(b.unmet_demand_percentage) -
        number(a.unmet_demand_percentage))
      .slice(0, 10);

    createChart("bedChart", {
      type: "bar",
      data: {
        labels: shortageStates.map(item => item.state),
        datasets: [{
          label: "Additional beds needed",
          data: shortageStates.map(state =>
            beds
              .filter(item => item.state === state.state)
              .reduce((sum, item) =>
                sum + number(item.additional_beds_needed), 0))
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: false }
        }
      }
    });

    createChart("fairnessChart", {
      type: "bar",
      data: {
        labels: shortageStates.map(item => item.state),
        datasets: [{
          label: "Hospitals with unmet demand (%)",
          data: shortageStates.map(item =>
            number(item.unmet_demand_percentage))
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: false }
        },
        scales: {
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: "Percentage"
            }
          }
        }
      }
    });

    createChart("featureChart", {
      type: "doughnut",
      data: {
        labels: features.map(item =>
          item.feature || item.Feature || item.name || "Feature"),
        datasets: [{
          label: "Feature importance",
          data: features.map(item =>
            number(item.importance ?? item.Importance ?? item.value))
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: "bottom" }
        }
      }
    });

    renderTable("bedTable", beds
      .slice()
      .sort((a, b) =>
        number(b.additional_beds_needed) -
        number(a.additional_beds_needed)));

    renderTable("fairnessTable", fairness
      .slice()
      .sort((a, b) =>
        number(b.unmet_demand_percentage) -
        number(a.unmet_demand_percentage)));

    renderTable("explanationTable", explanations);

    const reportList = document.getElementById("reportList");

    if (reportList) {
      reportList.innerHTML = [
        downloadLink(files.forecast, "Hospital demand forecasts"),
        downloadLink(files.beds, "Bed optimization results"),
        downloadLink(files.fairness, "Geographic fairness audit"),
        downloadLink(files.metrics, "Model evaluation metrics"),
        downloadLink(files.features, "Feature importance"),
        downloadLink(files.explanations, "Hospital explanations"),
        downloadLink("../output/graphs/model_comparison.png", "Model comparison chart"),
        downloadLink("../output/graphs/top_10_bed_shortages.png", "Top 10 bed shortages chart"),
        downloadLink("../output/graphs/geographic_fairness.png", "Geographic fairness chart")
      ].map(link => `<li>${link}</li>`).join("");
    }

    const status = document.getElementById("dataStatus");
    if (status) status.textContent = "Project data loaded successfully.";

  } catch (error) {
    console.error(error);
    const status = document.getElementById("dataStatus");
    if (status) {
      status.textContent = "Unable to load project data. Check the CSV files and server.";
    }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  loadDashboard();

  const refreshButton = document.getElementById("refreshBtn");
  if (refreshButton) {
    refreshButton.addEventListener("click", loadDashboard);
  }
});
cd /workspaces/hospital-resources-pig-study
python -m http.server 8000cd /workspaces/hospital-resources-pig-study
git status --short