import '@testing-library/jest-dom/vitest'

// jsdom doesn't implement scrollIntoView; MessageList calls it on every render.
if (typeof Element !== 'undefined' && !Element.prototype.scrollIntoView) {
  Element.prototype.scrollIntoView = () => {}
}
