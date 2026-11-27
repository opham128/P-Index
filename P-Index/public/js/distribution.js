// distribution.js — histograms with normal-curve overlay
// Raw data embedded (CSV is not exposed). Bin values are in original 0–100 scale.

const rawDistribution = [{"bin":13,"freq":1},{"bin":19,"freq":1},{"bin":20,"freq":2},{"bin":22,"freq":2},{"bin":23,"freq":2},{"bin":24,"freq":2},{"bin":25,"freq":1},{"bin":26,"freq":3},{"bin":27,"freq":1},{"bin":28,"freq":3},{"bin":29,"freq":3},{"bin":30,"freq":4},{"bin":31,"freq":3},{"bin":32,"freq":5},{"bin":33,"freq":4},{"bin":34,"freq":5},{"bin":35,"freq":4},{"bin":36,"freq":4},{"bin":37,"freq":6},{"bin":38,"freq":6},{"bin":39,"freq":8},{"bin":40,"freq":9},{"bin":41,"freq":6},{"bin":42,"freq":7},{"bin":43,"freq":13},{"bin":44,"freq":10},{"bin":45,"freq":11},{"bin":46,"freq":12},{"bin":47,"freq":8},{"bin":48,"freq":8},{"bin":49,"freq":6},{"bin":50,"freq":8},{"bin":51,"freq":14},{"bin":52,"freq":11},{"bin":53,"freq":4},{"bin":54,"freq":13},{"bin":55,"freq":6},{"bin":56,"freq":10},{"bin":57,"freq":7},{"bin":58,"freq":8},{"bin":59,"freq":11},{"bin":60,"freq":9},{"bin":61,"freq":10},{"bin":62,"freq":4},{"bin":63,"freq":8},{"bin":64,"freq":4},{"bin":65,"freq":6},{"bin":66,"freq":2},{"bin":67,"freq":5},{"bin":68,"freq":6},{"bin":69,"freq":3},{"bin":70,"freq":3},{"bin":71,"freq":4},{"bin":72,"freq":1},{"bin":73,"freq":5},{"bin":74,"freq":4},{"bin":76,"freq":2},{"bin":77,"freq":1},{"bin":78,"freq":1},{"bin":79,"freq":1},{"bin":80,"freq":2},{"bin":81,"freq":2},{"bin":82,"freq":1},{"bin":86,"freq":1},{"bin":88,"freq":1},{"bin":89,"freq":1},{"bin":97,"freq":1}];

const adjustedDistribution = [{"bin":15,"freq":1},{"bin":16,"freq":1},{"bin":19,"freq":1},{"bin":21,"freq":2},{"bin":22,"freq":3},{"bin":23,"freq":3},{"bin":25,"freq":2},{"bin":26,"freq":2},{"bin":27,"freq":4},{"bin":28,"freq":1},{"bin":29,"freq":7},{"bin":30,"freq":3},{"bin":31,"freq":5},{"bin":32,"freq":2},{"bin":33,"freq":6},{"bin":34,"freq":4},{"bin":35,"freq":5},{"bin":36,"freq":9},{"bin":37,"freq":8},{"bin":38,"freq":8},{"bin":39,"freq":6},{"bin":40,"freq":5},{"bin":41,"freq":10},{"bin":42,"freq":7},{"bin":43,"freq":4},{"bin":44,"freq":10},{"bin":45,"freq":13},{"bin":46,"freq":10},{"bin":47,"freq":6},{"bin":48,"freq":9},{"bin":49,"freq":10},{"bin":50,"freq":12},{"bin":51,"freq":8},{"bin":52,"freq":8},{"bin":53,"freq":7},{"bin":54,"freq":10},{"bin":55,"freq":6},{"bin":56,"freq":3},{"bin":57,"freq":8},{"bin":58,"freq":7},{"bin":59,"freq":7},{"bin":60,"freq":12},{"bin":61,"freq":12},{"bin":62,"freq":6},{"bin":63,"freq":4},{"bin":64,"freq":4},{"bin":65,"freq":8},{"bin":66,"freq":4},{"bin":67,"freq":5},{"bin":68,"freq":6},{"bin":69,"freq":1},{"bin":70,"freq":3},{"bin":71,"freq":6},{"bin":72,"freq":2},{"bin":73,"freq":2},{"bin":74,"freq":4},{"bin":75,"freq":2},{"bin":76,"freq":1},{"bin":77,"freq":1},{"bin":78,"freq":1},{"bin":79,"freq":3},{"bin":81,"freq":3},{"bin":82,"freq":1},{"bin":83,"freq":1},{"bin":86,"freq":1},{"bin":89,"freq":2},{"bin":91,"freq":1},{"bin":97,"freq":1}];

// ── helpers ──────────────────────────────────────────────────────────────────

const BIN_W = 3; // bin width in original 0–100 units → 0.03 in 0–1 scale

/** Re-bucket raw per-integer bins into BIN_W-wide bins; return all 0–100 slots */
function buildBins(dist) {
  const map = {};
  for (let b = 0; b < 100; b += BIN_W) map[b] = 0;
  dist.forEach(d => {
    const key = Math.floor(d.bin / BIN_W) * BIN_W;
    if (key in map) map[key] += d.freq;
  });
  return Object.entries(map)
    .sort((a, b) => +a[0] - +b[0])
    .map(([start, freq]) => ({ center: (+start + BIN_W / 2) / 100, freq }));
}

// Exact summary stats (0–1 scale) computed from the unrounded CSV columns:
//   PI   (col 27): n = 340, mean = 0.51213048471, sample std = 0.139096061766 (pop std = 0.138891358106)
//   OWPI (col 31): n = 340, mean = 0.509291658248, sample std = 0.147372329089 (pop std = 0.147155445485)
const rawStats      = { mean: 0.51213048471,  std: 0.139096061766, total: 340 };
const adjustedStats = { mean: 0.509291658248, std: 0.147372329089, total: 340 };

function normalPDF(x, mean, std) {
  return Math.exp(-0.5 * Math.pow((x - mean) / std, 2)) / (std * Math.sqrt(2 * Math.PI));
}

/** Smooth normal-curve points across full 0–1 range */
function normalCurve(mean, std, total) {
  const pts = [];
  for (let i = 0; i <= 200; i++) {
    const x = i / 200;
    // Scale PDF so its area equals total histogram area (total * bin_width_in_0-1)
    pts.push({ x, y: normalPDF(x, mean, std) * total * (BIN_W / 100) });
  }
  return pts;
}

// ── chart factory ─────────────────────────────────────────────────────────────

function createHistogram(canvasId, dist, stats, title, barColor) {
  const ctx = document.getElementById(canvasId)?.getContext('2d');
  if (!ctx) return;

  const bins  = buildBins(dist);
  const curve = normalCurve(stats.mean, stats.std, stats.total);

  const meanLabel = stats.mean.toFixed(3);
  const stdLabel  = stats.std.toFixed(3);

  new Chart(ctx, {
    data: {
      datasets: [
        {
          type: 'bar',
          label: 'Frequency',
          data: bins.map(b => ({ x: b.center, y: b.freq })),
          backgroundColor: barColor,
          borderColor: barColor.replace(/[\d.]+\)$/, '1)'),
          borderWidth: 1,
          barPercentage: 1.0,
          categoryPercentage: 1.0,
          order: 2
        },
        {
          type: 'line',
          label: `Normal (μ = ${meanLabel}, σ = ${stdLabel}, n = ${stats.total})`,
          data: curve,
          borderColor: 'rgba(220,38,38,0.85)',
          borderWidth: 2.5,
          pointRadius: 0,
          fill: false,
          tension: 0.4,
          order: 1
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: {
          display: true,
          text: title,
          font: { size: 15, weight: '600', family: 'Manrope' },
          color: '#091426',
          padding: { bottom: 14 }
        },
        legend: {
          display: true,
          labels: { usePointStyle: true, font: { family: 'Manrope', size: 12 }, boxWidth: 12 }
        },
        tooltip: {
          callbacks: {
            title: items => `p-Index ≈ ${(+items[0].parsed.x).toFixed(2)}`,
            label: item => item.dataset.type === 'bar'
              ? `Count: ${item.parsed.y}`
              : `Normal (scaled): ${item.parsed.y.toFixed(2)}`
          }
        }
      },
      scales: {
        x: {
          type: 'linear',
          min: 0,
          max: 1,
          title: {
            display: true,
            text: 'p‑Index (0 – 1 scale)',
            font: { family: 'Manrope', size: 12 },
            color: '#475569'
          },
          ticks: {
            stepSize: 0.1,
            callback: v => v.toFixed(1),
            font: { family: 'Manrope', size: 11 }
          },
          grid: { color: 'rgba(0,0,0,0.05)' }
        },
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Frequency',
            font: { family: 'Manrope', size: 12 },
            color: '#475569'
          },
          ticks: { font: { family: 'Manrope', size: 11 } },
          grid: { color: 'rgba(0,0,0,0.06)' }
        }
      }
    }
  });
}

// ── percentile (against original integer bins, value entered in 0–1 scale) ──

function computePercentile(value01, dist) {
  const val100 = value01 * 100; // convert input back to 0-100 scale for lookup
  const total  = dist.reduce((s, d) => s + d.freq, 0);
  const below  = dist.reduce((s, d) => s + (d.bin < val100 ? d.freq : 0), 0);
  const at     = dist.find(d => Math.abs(d.bin - val100) < 0.5)?.freq || 0;
  return ((below + at) / total * 100).toFixed(1);
}

// ── public API ────────────────────────────────────────────────────────────────

window.pIndexDistribution = {
  init() {
    createHistogram('raw_distribution_chart',      rawDistribution,      rawStats,      'p‑Index Distribution',                     'rgba(59,130,246,0.55)');
    createHistogram('adjusted_distribution_chart', adjustedDistribution, adjustedStats, 'Authorship‑Adjusted p‑Index Distribution', 'rgba(16,185,129,0.55)');

    // Wire percentile inputs (users enter values in 0–1 scale)
    function hookInput(inputId, spanId, distArr) {
      const inp  = document.getElementById(inputId);
      const span = document.getElementById(spanId);
      if (!inp || !span) return;
      inp.addEventListener('input', () => {
        const v = parseFloat(inp.value);
        span.textContent = (!isNaN(v) && v >= 0 && v <= 1)
          ? `→ ${computePercentile(v, distArr)}th percentile`
          : '';
      });
    }

    hookInput('raw_input',      'raw_percentile',      rawDistribution);
    hookInput('adjusted_input', 'adjusted_percentile', adjustedDistribution);
  },

  percentileForRaw:      v => computePercentile(v, rawDistribution),
  percentileForAdjusted: v => computePercentile(v, adjustedDistribution)
};
