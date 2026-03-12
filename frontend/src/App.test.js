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
})
