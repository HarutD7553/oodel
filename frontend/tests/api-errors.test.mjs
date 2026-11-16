import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import test from 'node:test'
import vm from 'node:vm'

const context = vm.createContext({})
const source = await readFile(resolve(import.meta.dirname, '../../api-errors.js'), 'utf8')
vm.runInContext(source, context)
const { fromResponse, fieldMessage, itemMessages } = context.OodelApiErrors

test('preserves the API detail, status, and structured field errors', () => {
  const error = fromResponse({
    detail: 'Enter a valid email address.',
    errors: { email: ['Enter a valid email address.'] },
  }, 400)

  assert.equal(error.message, 'Enter a valid email address.')
  assert.equal(error.kind, 'http')
  assert.equal(error.status, 400)
  assert.equal(fieldMessage(error, 'email'), 'Enter a valid email address.')
})

test('uses a nested validation message when detail is missing', () => {
  const error = fromResponse({ errors: { password: ['This password is too common.'] } }, 400)

  assert.equal(error.message, 'This password is too common.')
  assert.equal(fieldMessage(error, 'password'), 'This password is too common.')
})

test('labels nested order item errors with the matching cart item', () => {
  const error = fromResponse({
    detail: 'Unknown cake flavor.',
    errors: { items: [{ detail: ['Unknown cake flavor.'] }, {}] },
  }, 400)

  assert.deepEqual(
    Array.from(itemMessages(error, [{ name: 'Strawberry Cake' }, { name: 'Croissant' }]), item => ({ ...item })),
    [{ index: 0, label: 'Strawberry Cake', message: 'Unknown cake flavor.' }],
  )
})

test('falls back safely for a non-JSON error response', () => {
  const error = fromResponse(null, 502)

  assert.equal(error.message, 'The server could not complete that request.')
  assert.deepEqual({ ...error.errors }, {})
})
