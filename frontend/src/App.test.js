import { flushPromises, mount } from '@vue/test-utils'
import { vi } from 'vitest'

import App from './App.vue'

const etfResponse = {
  items: [
    {
      ticker: 'VTI',
      name: 'Vanguard Total Stock Market ETF',
      holdings_count: 3000,
      data_as_of_date: '2026-03-12',
      last_refreshed_at: '2026-03-12T08:00:00+00:00',
    },
  ],
}

const priceResponse = {
  items: [
    {
      ticker: 'VTI',
      price: 287.45,
      price_date: '2026-03-12',
      fetched_at: '2026-03-12T08:05:00+00:00',
    },
  ],
}

const prepareResponse = {
  etfs: [
    {
      ticker: 'VTI',
      updated: true,
      holdings_count: 3000,
      data_as_of_date: '2026-03-12',
      last_refreshed_at: '2026-03-12T08:00:00+00:00',
    },
  ],
  prices: [
    {
      ticker: 'VTI',
      updated: true,
      price: 287.45,
      price_date: '2026-03-12',
      fetched_at: '2026-03-12T08:05:00+00:00',
    },
    {
      ticker: 'MSFT',
      updated: true,
      price: 410.25,
      price_date: '2026-03-12',
      fetched_at: '2026-03-12T08:05:00+00:00',
    },
  ],
}

const analyzeResponse = {
  threshold_percent: 5,
  rows: [
    { ticker: 'MSFT', total_percent: 31.4, from_etf_percent: 18.9, direct_percent: 12.5 },
    { ticker: 'AAPL', total_percent: 18.2, from_etf_percent: 12.2, direct_percent: 6.0 },
  ],
}

function createFetchMock() {
  return vi.fn(async (url, options = {}) => {
    if (url === '/api/etfs' && (!options.method || options.method === 'GET')) {
      return { ok: true, json: async () => etfResponse }
    }

    if (url === '/api/prices' && (!options.method || options.method === 'GET')) {
      return { ok: true, json: async () => priceResponse }
    }

    if (url === '/api/cache/prepare' && options.method === 'POST') {
      return { ok: true, json: async () => prepareResponse }
    }

    if (url === '/api/analyze' && options.method === 'POST') {
      return { ok: true, json: async () => analyzeResponse }
    }

    return { ok: false, json: async () => ({ detail: `Unhandled request: ${url}` }) }
  })
}

async function mountApp() {
  const wrapper = mount(App)
  await flushPromises()
  return wrapper
}

describe('App', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', createFetchMock())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
  })

  test('renders the hero copy and action buttons', async () => {
    const wrapper = await mountApp()

    expect(wrapper.text()).toContain('See what your stock portfolio really holds')
    expect(wrapper.text()).toContain('Analyze stock exposure across ETFs and direct holdings.')
    expect(wrapper.text()).toContain('Refresh Market Data')
    expect(wrapper.text()).toContain('Analyze Portfolio')
  })

  test('renders default holdings and output shell', async () => {
    const wrapper = await mountApp()
    const tickerInputs = wrapper.findAll('input[type="text"]')

    expect(wrapper.findAll('.holding-grid').length).toBeGreaterThan(4)
    expect(tickerInputs[0].element.value).toBe('VTI')
    expect(wrapper.text()).toContain('Exposure Table')
    expect(wrapper.text()).toContain('No exposure rows yet')
  })

  test('pressing enter on an input confirms by blurring the field', async () => {
    const wrapper = await mountApp()
    const tickerInput = wrapper.find('input[type="text"]')
    const blurSpy = vi.spyOn(tickerInput.element, 'blur')

    await tickerInput.trigger('keydown.enter')

    expect(blurSpy).toHaveBeenCalled()
  })

  test('adds a new holding row when add row is clicked', async () => {
    const wrapper = await mountApp()

    await wrapper.find('.ghost-button').trigger('click')

    const tickerInputs = wrapper.findAll('input[type="text"]')
    const shareInputs = wrapper.findAll('input[type="number"]')

    expect(tickerInputs).toHaveLength(5)
    expect(tickerInputs[4].element.value).toBe('')
    expect(shareInputs[4].element.value).toBe('0')
    expect(wrapper.find('.holdings-scrollable').exists()).toBe(true)
  })

  test('removes a holding row when remove is clicked', async () => {
    const wrapper = await mountApp()

    await wrapper.findAll('.icon-button')[1].trigger('click')

    const tickerInputs = wrapper.findAll('input[type="text"]')
    const tickerValues = tickerInputs.map((input) => input.element.value)

    expect(tickerInputs).toHaveLength(3)
    expect(tickerValues).not.toContain('MSFT')
  })

  test('keeps one row when attempting to remove the final holding', async () => {
    const wrapper = await mountApp()

    for (let index = 0; index < 3; index += 1) {
      await wrapper.findAll('.icon-button')[0].trigger('click')
    }
    await wrapper.find('.icon-button').trigger('click')

    expect(wrapper.findAll('input[type="text"]')).toHaveLength(1)
  })

  test('updates the threshold label when the slider changes', async () => {
    const wrapper = await mountApp()
    const slider = wrapper.find('input[type="range"]')

    await slider.setValue(12)

    expect(wrapper.text()).toContain('12%')
  })

  test('refreshes market data and shows success status', async () => {
    const wrapper = await mountApp()

    await wrapper.find('.secondary-button').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('Market data is ready.')
  })

  test('analyzes portfolio and renders exposure rows', async () => {
    const wrapper = await mountApp()

    await wrapper.find('.primary-button').trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('Analysis updated for 5% threshold.')
    expect(wrapper.text()).toContain('31.4')
    expect(wrapper.text()).toContain('18.2')
  })
})
