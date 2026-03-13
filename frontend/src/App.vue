<script setup>
import { computed, onMounted, ref } from 'vue'

const holdings = ref([
  { id: 1, ticker: 'VTI', shares: 3 },
  { id: 2, ticker: 'MSFT', shares: 10 },
  { id: 3, ticker: 'AAPL', shares: 4 },
  { id: 4, ticker: 'NVDA', shares: 2 },
])
const thresholdPercent = ref(5)
const exposureRows = ref([])
const etfOptions = ref([])
const priceOptions = ref([])
const appError = ref('')
const statusMessage = ref('')
const isRefreshing = ref(false)
const isAnalyzing = ref(false)

let nextHoldingId = 5

function barWidth(percent) {
  return `${Math.max(percent, 2)}%`
}

function confirmField(event) {
  event.target.blur()
}

function addRow() {
  holdings.value.push({
    id: nextHoldingId,
    ticker: '',
    shares: 0,
  })
  nextHoldingId += 1
}

function removeRow(holdingId) {
  if (holdings.value.length === 1) {
    return
  }

  holdings.value = holdings.value.filter((holding) => holding.id !== holdingId)
}

const holdingsScrollClass = computed(() => ({
  'holdings-scroll': true,
  'holdings-scrollable': holdings.value.length > 4,
}))

const sanitizedHoldings = computed(() =>
  holdings.value
    .map((holding) => ({
      ticker: holding.ticker.trim().toUpperCase(),
      shares: Number(holding.shares),
    }))
    .filter((holding) => holding.ticker && holding.shares > 0)
)

const chartRows = computed(() => exposureRows.value.slice(0, 6).map((row) => ({
  ticker: row.ticker,
  percent: row.total_percent,
})))

const etfAsOfLabel = computed(() => {
  const dated = etfOptions.value.find((item) => item.data_as_of_date)
  return dated ? `ETF data as of ${dated.data_as_of_date}` : 'ETF data not loaded'
})

const priceAsOfLabel = computed(() => {
  const dated = priceOptions.value.find((item) => item.price_date)
  return dated ? `Prices as of ${dated.price_date}` : 'Prices not loaded'
})

async function apiRequest(path, options = {}) {
  const response = await fetch(`/api${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  })

  const data = await response.json()
  if (!response.ok) {
    throw new Error(data.detail || 'Request failed')
  }
  return data
}

async function loadStatus() {
  try {
    const [etfData, priceData] = await Promise.all([
      apiRequest('/etfs', { method: 'GET' }),
      apiRequest('/prices', { method: 'GET' }),
    ])
    etfOptions.value = etfData.items
    priceOptions.value = priceData.items
  } catch (error) {
    appError.value = error.message
  }
}

async function refreshMarketData() {
  if (!sanitizedHoldings.value.length) {
    appError.value = 'Enter at least one holding with shares above 0.'
    return
  }

  appError.value = ''
  statusMessage.value = ''
  isRefreshing.value = true

  try {
    const data = await apiRequest('/cache/prepare', {
      method: 'POST',
      body: JSON.stringify({ holdings: sanitizedHoldings.value }),
    })
    etfOptions.value = data.etfs.map((item) => ({
      ticker: item.ticker,
      name: item.ticker,
      holdings_count: item.holdings_count,
      data_as_of_date: item.data_as_of_date,
      last_refreshed_at: item.last_refreshed_at,
    }))
    priceOptions.value = data.prices.map((item) => ({
      ticker: item.ticker,
      price: item.price,
      price_date: item.price_date,
      fetched_at: item.fetched_at,
    }))
    statusMessage.value = 'Market data is ready.'
  } catch (error) {
    appError.value = error.message
  } finally {
    isRefreshing.value = false
  }
}

async function analyzePortfolio() {
  if (!sanitizedHoldings.value.length) {
    appError.value = 'Enter at least one holding with shares above 0.'
    return
  }

  appError.value = ''
  statusMessage.value = ''
  isAnalyzing.value = true

  try {
    const data = await apiRequest('/analyze', {
      method: 'POST',
      body: JSON.stringify({
        holdings: sanitizedHoldings.value,
        threshold_percent: Number(thresholdPercent.value),
      }),
    })
    exposureRows.value = data.rows
    statusMessage.value = `Analysis updated for ${data.threshold_percent}% threshold.`
    await loadStatus()
  } catch (error) {
    appError.value = error.message
  } finally {
    isAnalyzing.value = false
  }
}

onMounted(async () => {
  await loadStatus()
})
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
        </div>

        <div class="card">
          <div class="card-heading">
            <h3>Holdings</h3>
            <button
              class="ghost-button"
              type="button"
              title="Add another stock or ETF holding to the portfolio."
              @click="addRow"
            >
              + Add Row
            </button>
          </div>

          <div :class="holdingsScrollClass">
            <div class="holding-grid holding-grid-head">
              <span>Ticker</span>
              <span>Shares</span>
              <span>Action</span>
            </div>

            <div
              v-for="holding in holdings"
              :key="holding.id"
              class="holding-grid"
            >
              <label class="field">
                <span class="sr-only">Ticker</span>
                <input
                  v-model="holding.ticker"
                  type="text"
                  @keydown.enter="confirmField"
                />
              </label>

              <label class="field">
                <span class="sr-only">Shares</span>
                <input
                  v-model.number="holding.shares"
                  type="number"
                  min="0"
                  @keydown.enter="confirmField"
                />
              </label>

              <button
                class="icon-button"
                type="button"
                aria-label="Remove row"
                title="Remove this holding from the portfolio."
                @click="removeRow(holding.id)"
              >
                <span aria-hidden="true">X</span>
              </button>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="card-heading">
            <h3>Display Threshold</h3>
            <span class="value-pill">{{ thresholdPercent }}%</span>
          </div>

          <label class="range-block">
            <span>Show positions at or above this percentage.</span>
            <input v-model="thresholdPercent" type="range" min="1" max="100" />
          </label>
        </div>

        <div class="actions">
          <button
            class="secondary-button"
            type="button"
            title="Fetch the latest ETF holdings and daily prices for this portfolio."
            :disabled="isRefreshing"
            @click="refreshMarketData"
          >
            {{ isRefreshing ? 'Refreshing...' : 'Refresh Market Data' }}
          </button>
          <button
            class="primary-button"
            type="button"
            title="Run the portfolio exposure analysis using cached market data."
            :disabled="isAnalyzing"
            @click="analyzePortfolio"
          >
            {{ isAnalyzing ? 'Analyzing...' : 'Analyze Portfolio' }}
          </button>
        </div>

        <p v-if="statusMessage" class="feedback success">{{ statusMessage }}</p>
        <p v-if="appError" class="feedback error">{{ appError }}</p>
      </aside>

      <section class="panel panel-right">
        <div class="panel-header">
          <div>
            <p class="panel-kicker">Output</p>
            <h2>Exposure View</h2>
          </div>
          <div class="meta-stack">
            <span class="meta-chip">{{ etfAsOfLabel }}</span>
            <span class="meta-chip">{{ priceAsOfLabel }}</span>
          </div>
        </div>

        <div class="card chart-card">
          <div class="card-heading">
            <h3>Exposure Breakdown</h3>
            <span class="chart-note">Top positions by total portfolio exposure</span>
          </div>

          <div v-if="chartRows.length" class="chart-list">
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
          <p v-else class="empty-state">
            Run an analysis to populate the chart.
          </p>
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
              <tbody v-if="exposureRows.length">
                <tr v-for="row in exposureRows" :key="row.ticker">
                  <td>{{ row.ticker }}</td>
                  <td>{{ row.total_percent.toFixed(1) }}</td>
                  <td>{{ row.from_etf_percent.toFixed(1) }}</td>
                  <td>{{ row.direct_percent.toFixed(1) }}</td>
                </tr>
              </tbody>
              <tbody v-else>
                <tr>
                  <td colspan="4" class="empty-cell">No exposure rows yet. Refresh data, then analyze.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </section>
  </main>
</template>
