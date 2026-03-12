<script setup>
const holdings = [
  { ticker: 'VTI', shares: 3 },
  { ticker: 'MSFT', shares: 10 },
  { ticker: 'AAPL', shares: 4 },
]

const chartRows = [
  { ticker: 'MSFT', percent: 31.4 },
  { ticker: 'AAPL', percent: 18.2 },
  { ticker: 'NVDA', percent: 11.6 },
  { ticker: 'AMZN', percent: 8.4 },
]

const exposureRows = [
  { ticker: 'MSFT', total: 31.4, etf: 18.9, direct: 12.5 },
  { ticker: 'AAPL', total: 18.2, etf: 12.2, direct: 6.0 },
  { ticker: 'NVDA', total: 11.6, etf: 11.6, direct: 0.0 },
  { ticker: 'AMZN', total: 8.4, etf: 8.4, direct: 0.0 },
]

function barWidth(percent) {
  return `${Math.max(percent, 2)}%`
}
</script>

<template>
  <main class="shell">
    <section class="hero">
      <p class="eyebrow">stockVis</p>
      <h1>See what your stock portfolio really holds</h1>
      <p class="hero-copy">
        Analyze stock exposure across ETFs and direct holdings.
      </p>
    </section>

    <section class="workspace">
      <aside class="panel panel-left">
        <div class="panel-header">
          <div>
            <p class="panel-kicker">Inputs</p>
            <h2>Portfolio Builder</h2>
          </div>
          <span class="status-pill">Draft</span>
        </div>

        <div class="card">
          <div class="card-heading">
            <h3>Holdings</h3>
            <button class="ghost-button" type="button">+ Add Row</button>
          </div>

          <div class="holding-grid holding-grid-head">
            <span>Ticker</span>
            <span>Shares</span>
            <span>Action</span>
          </div>

          <div
            v-for="holding in holdings"
            :key="`${holding.ticker}-${holding.shares}`"
            class="holding-grid"
          >
            <label class="field">
              <span class="sr-only">Ticker</span>
              <input :value="holding.ticker" type="text" />
            </label>

            <label class="field">
              <span class="sr-only">Shares</span>
              <input :value="holding.shares" type="number" min="1" />
            </label>

            <button class="icon-button" type="button" aria-label="Remove row">x</button>
          </div>
        </div>

        <div class="card">
          <div class="card-heading">
            <h3>Display Threshold</h3>
            <span class="value-pill">5%</span>
          </div>

          <label class="range-block">
            <span>Show positions at or above this percentage.</span>
            <input type="range" min="1" max="100" value="5" />
          </label>
        </div>

        <div class="actions">
          <button class="secondary-button" type="button">Prepare Cache</button>
          <button class="primary-button" type="button">Analyze Portfolio</button>
        </div>
      </aside>

      <section class="panel panel-right">
        <div class="panel-header">
          <div>
            <p class="panel-kicker">Output</p>
            <h2>Exposure View</h2>
          </div>
          <div class="meta-stack">
            <span class="meta-chip">ETF data as of 2026-03-11</span>
            <span class="meta-chip">Prices as of 2026-03-11</span>
          </div>
        </div>

        <div class="card chart-card">
          <div class="card-heading">
            <h3>Exposure Breakdown</h3>
            <span class="chart-note">Top positions by total portfolio exposure</span>
          </div>

          <div class="chart-list">
            <div v-for="row in chartRows" :key="row.ticker" class="chart-row">
              <div class="chart-label">
                <strong>{{ row.ticker }}</strong>
                <span>{{ row.percent.toFixed(1) }}%</span>
              </div>
              <div class="bar-track">
                <div class="bar-fill" :style="{ width: barWidth(row.percent) }"></div>
              </div>
            </div>
          </div>
        </div>

        <div class="card table-card">
          <div class="card-heading">
            <h3>Exposure Table</h3>
            <span class="chart-note">Filtered above threshold and sorted by total exposure</span>
          </div>

          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Ticker</th>
                  <th>Total %</th>
                  <th>ETF %</th>
                  <th>Direct %</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in exposureRows" :key="row.ticker">
                  <td>{{ row.ticker }}</td>
                  <td>{{ row.total.toFixed(1) }}</td>
                  <td>{{ row.etf.toFixed(1) }}</td>
                  <td>{{ row.direct.toFixed(1) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </section>
  </main>
</template>
