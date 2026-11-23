// distribution.js - render p-index distribution charts and percentile calculation

// Histogram data derived from the uploaded CSV (embedded, CSV not exposed)
const rawDistribution = [{"bin":13,"freq":1},{"bin":19,"freq":1},{"bin":20,"freq":2},{"bin":22,"freq":2},{"bin":23,"freq":2},{"bin":24,"freq":2},{"bin":25,"freq":1},{"bin":26,"freq":3},{"bin":27,"freq":1},{"bin":28,"freq":3},{"bin":29,"freq":3},{"bin":30,"freq":4},{"bin":31,"freq":3},{"bin":32,"freq":5},{"bin":33,"freq":4},{"bin":34,"freq":5},{"bin":35,"freq":4},{"bin":36,"freq":4},{"bin":37,"freq":6},{"bin":38,"freq":6},{"bin":39,"freq":8},{"bin":40,"freq":9},{"bin":41,"freq":6},{"bin":42,"freq":7},{"bin":43,"freq":13},{"bin":44,"freq":10},{"bin":45,"freq":11},{"bin":46,"freq":12},{"bin":47,"freq":8},{"bin":48,"freq":8},{"bin":49,"freq":6},{"bin":50,"freq":8},{"bin":51,"freq":14},{"bin":52,"freq":11},{"bin":53,"freq":4},{"bin":54,"freq":13},{"bin":55,"freq":6},{"bin":56,"freq":10},{"bin":57,"freq":7},{"bin":58,"freq":8},{"bin":59,"freq":11},{"bin":60,"freq":9},{"bin":61,"freq":10},{"bin":62,"freq":4},{"bin":63,"freq":8},{"bin":64,"freq":4},{"bin":65,"freq":6},{"bin":66,"freq":2},{"bin":67,"freq":5},{"bin":68,"freq":6},{"bin":69,"freq":3},{"bin":70,"freq":3},{"bin":71,"freq":4},{"bin":72,"freq":1},{"bin":73,"freq":5},{"bin":74,"freq":4},{"bin":76,"freq":2},{"bin":77,"freq":1},{"bin":78,"freq":1},{"bin":79,"freq":1},{"bin":80,"freq":2},{"bin":81,"freq":2},{"bin":82,"freq":1},{"bin":86,"freq":1},{"bin":88,"freq":1},{"bin":89,"freq":1},{"bin":97,"freq":1}];

const adjustedDistribution = [{"bin":15,"freq":1},{"bin":16,"freq":1},{"bin":19,"freq":1},{"bin":21,"freq":2},{"bin":22,"freq":3},{"bin":23,"freq":3},{"bin":25,"freq":2},{"bin":26,"freq":2},{"bin":27,"freq":4},{"bin":28,"freq":1},{"bin":29,"freq":7},{"bin":30,"freq":3},{"bin":31,"freq":5},{"bin":32,"freq":2},{"bin":33,"freq":6},{"bin":34,"freq":4},{"bin":35,"freq":5},{"bin":36,"freq":9},{"bin":37,"freq":8},{"bin":38,"freq":8},{"bin":39,"freq":6},{"bin":40,"freq":5},{"bin":41,"freq":10},{"bin":42,"freq":7},{"bin":43,"freq":4},{"bin":44,"freq":10},{"bin":45,"freq":13},{"bin":46,"freq":10},{"bin":47,"freq":6},{"bin":48,"freq":9},{"bin":49,"freq":10},{"bin":50,"freq":12},{"bin":51,"freq":8},{"bin":52,"freq":8},{"bin":53,"freq":7},{"bin":54,"freq":10},{"bin":55,"freq":6},{"bin":56,"freq":3},{"bin":57,"freq":8},{"bin":58,"freq":7},{"bin":59,"freq":7},{"bin":60,"freq":12},{"bin":61,"freq":12},{"bin":62,"freq":6},{"bin":63,"freq":4},{"bin":64,"freq":4},{"bin":65,"freq":8},{"bin":66,"freq":4},{"bin":67,"freq":5},{"bin":68,"freq":6},{"bin":69,"freq":1},{"bin":70,"freq":3},{"bin":71,"freq":6},{"bin":72,"freq":2},{"bin":73,"freq":2},{"bin":74,"freq":4},{"bin":75,"freq":2},{"bin":76,"freq":1},{"bin":77,"freq":1},{"bin":78,"freq":1},{"bin":79,"freq":3},{"bin":81,"freq":3},{"bin":82,"freq":1},{"bin":83,"freq":1},{"bin":86,"freq":1},{"bin":89,"freq":2},{"bin":91,"freq":1},{"bin":97,"freq":1}];

function createHistogram(ctx, data, title, color) {
  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: data.map(d => d.bin),
      datasets: [{
        label: 'Frequency',
        data: data.map(d => d.freq),
        backgroundColor: color,
        borderColor: color.replace('0.5', '1'),
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      plugins: {
        title: { display: true, text: title },
        legend: { display: false }
      },
      scales: {
        x: { title: { display: true, text: 'p‑Index' } },
        y: { title: { display: true, text: 'Frequency' }, beginAtZero: true }
      }
    }
  });
}

function computePercentile(value, distribution) {
  const total = distribution.reduce((sum, d) => sum + d.freq, 0);
  const below = distribution.reduce((sum, d) => sum + (d.bin < value ? d.freq : 0), 0);
  const equal = distribution.find(d => d.bin === value)?.freq || 0;
  return ((below + equal) / total) * 100;
}

window.pIndexDistribution = {
  init: function() {
    const rawCtx = document.getElementById('raw_distribution_chart')?.getContext('2d');
    const adjCtx = document.getElementById('adjusted_distribution_chart')?.getContext('2d');
    if (rawCtx) createHistogram(rawCtx, rawDistribution, 'p‑Index Distribution', 'rgba(59,130,246,0.5)');
    if (adjCtx) createHistogram(adjCtx, adjustedDistribution, 'Authorship‑Adjusted p‑Index Distribution', 'rgba(16,185,129,0.5)');
    // Hook up percentile inputs
    const rawInput = document.getElementById('raw_input');
    const rawPercentile = document.getElementById('raw_percentile');
    if (rawInput && rawPercentile) {
      rawInput.addEventListener('input', () => {
        const val = Number(rawInput.value);
        rawPercentile.textContent = isNaN(val) ? '' : pIndexDistribution.percentileForRaw(val) + '%';
      });
    }
    const adjInput = document.getElementById('adjusted_input');
    const adjPercentile = document.getElementById('adjusted_percentile');
    if (adjInput && adjPercentile) {
      adjInput.addEventListener('input', () => {
        const val = Number(adjInput.value);
        adjPercentile.textContent = isNaN(val) ? '' : pIndexDistribution.percentileForAdjusted(val) + '%';
      });
    }
  },

  percentileForRaw: function(value) { return computePercentile(value, rawDistribution).toFixed(1); },
  percentileForAdjusted: function(value) { return computePercentile(value, adjustedDistribution).toFixed(1); }
};
