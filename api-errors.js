(function exposeApiErrors(global) {
  class ApiError extends Error {
    constructor(message, kind, status, errors = {}) {
      super(message)
      this.name = 'ApiError'
      this.kind = kind
      this.status = status
      this.errors = errors
    }
  }

  function firstMessage(value) {
    if (Array.isArray(value)) {
      for (const item of value) {
        const message = firstMessage(item)
        if (message) return message
      }
      return ''
    }
    if (value && typeof value === 'object') {
      for (const item of Object.values(value)) {
        const message = firstMessage(item)
        if (message) return message
      }
      return ''
    }
    return typeof value === 'string' ? value : ''
  }

  function fromResponse(data, status, fallback = 'The server could not complete that request.') {
    const body = data && typeof data === 'object' ? data : {}
    const errors = body.errors && typeof body.errors === 'object' ? body.errors : {}
    const detail = typeof body.detail === 'string' ? body.detail.trim() : ''
    return new ApiError(detail || firstMessage(errors) || firstMessage(body) || fallback, 'http', status, errors)
  }

  function fieldMessage(error, field) {
    return firstMessage(error?.errors?.[field])
  }

  function itemMessages(error, items = []) {
    const itemErrors = error?.errors?.items
    if (!Array.isArray(itemErrors)) return []
    return itemErrors.flatMap((value, index) => {
      const message = firstMessage(value)
      if (!message) return []
      return [{ index, label: items[index]?.name || `Item ${index + 1}`, message }]
    })
  }

  global.OodelApiErrors = Object.freeze({ ApiError, firstMessage, fromResponse, fieldMessage, itemMessages })
})(globalThis)
