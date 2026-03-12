import { mount } from '@vue/test-utils'
import { vi } from 'vitest'

import App from './App.vue'


describe('App', () => {
  test('renders the hero copy and action buttons', () => {
    const wrapper = mount(App)

    expect(wrapper.text()).toContain('See what your stock portfolio really holds')
    expect(wrapper.text()).toContain('Analyze stock exposure across ETFs and direct holdings.')
    expect(wrapper.text()).toContain('Refresh Market Data')
    expect(wrapper.text()).toContain('Analyze Portfolio')
  })

  test('renders placeholder holdings and exposure rows', () => {
    const wrapper = mount(App)
    const tickerInputs = wrapper.findAll('input[type="text"]')

    expect(wrapper.findAll('.holding-grid').length).toBeGreaterThan(3)
    expect(tickerInputs[0].element.value).toBe('VTI')
    expect(wrapper.text()).toContain('MSFT')
    expect(wrapper.text()).toContain('Exposure Table')
  })

  test('pressing enter on an input confirms by blurring the field', async () => {
    const wrapper = mount(App)
    const tickerInput = wrapper.find('input[type="text"]')
    const blurSpy = vi.spyOn(tickerInput.element, 'blur')

    await tickerInput.trigger('keydown.enter')

    expect(blurSpy).toHaveBeenCalled()
  })

  test('adds a new holding row when add row is clicked', async () => {
    const wrapper = mount(App)

    await wrapper.find('.ghost-button').trigger('click')

    const tickerInputs = wrapper.findAll('input[type="text"]')
    const shareInputs = wrapper.findAll('input[type="number"]')

    expect(tickerInputs).toHaveLength(4)
    expect(tickerInputs[3].element.value).toBe('')
    expect(shareInputs[3].element.value).toBe('0')
  })

  test('removes a holding row when remove is clicked', async () => {
    const wrapper = mount(App)

    await wrapper.findAll('.icon-button')[1].trigger('click')

    const tickerInputs = wrapper.findAll('input[type="text"]')
    const tickerValues = tickerInputs.map((input) => input.element.value)

    expect(tickerInputs).toHaveLength(2)
    expect(tickerValues).not.toContain('MSFT')
  })

  test('keeps one row when attempting to remove the final holding', async () => {
    const wrapper = mount(App)

    for (let index = 0; index < 2; index += 1) {
      await wrapper.findAll('.icon-button')[0].trigger('click')
    }
    await wrapper.find('.icon-button').trigger('click')

    expect(wrapper.findAll('input[type="text"]')).toHaveLength(1)
  })

  test('updates the threshold label when the slider changes', async () => {
    const wrapper = mount(App)
    const slider = wrapper.find('input[type="range"]')

    await slider.setValue(12)

    expect(wrapper.text()).toContain('12%')
  })
})
