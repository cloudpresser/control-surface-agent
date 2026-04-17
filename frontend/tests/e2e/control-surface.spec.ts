import { expect, test } from '@playwright/test'

test.setTimeout(180000)

test('operator console runs workflow and records reconciliation', async ({ page }) => {
  await page.goto('/')

  await expect(page.getByRole('heading', { name: /supervised ai decision workflows/i })).toBeVisible()

  await page.screenshot({ path: 'test-artifacts/01-initial-console.png', fullPage: true })

  await page.getByRole('button', { name: 'Initialize Run' }).click()
  await expect(page.getByRole('button', { name: 'Reset Setup' })).toBeVisible({ timeout: 30000 })
  await expect(page.getByText('Intent appears after initialization.')).toHaveCount(0, { timeout: 30000 })
  await expect(page.getByText(/evaluate_opportunity/i)).toBeVisible({ timeout: 30000 })

  await page.getByRole('button', { name: 'Run All' }).click()

  await expect(page.getByText(/scope: full/i)).toBeVisible({ timeout: 60000 })
  await expect(page.getByText(/^(conditionally_pursue|pursue)$/)).toBeVisible({ timeout: 60000 })

  await page.screenshot({ path: 'test-artifacts/02-post-run-console.png', fullPage: true })

  const operatorControls = page.getByTestId('operator-controls-panel')

  await page.getByRole('button', { name: 'Apply Feedback' }).click()
  await expect(operatorControls.locator('.stacked-list .list-item strong').first()).toHaveText('force_retrieval', { timeout: 30000 })

  await page.getByRole('button', { name: 'Re-run' }).click()
  await expect(page.getByText(/Expand Trace|Collapse Trace/i)).toBeVisible({ timeout: 60000 })

  await page.screenshot({ path: 'test-artifacts/03-post-feedback-console.png', fullPage: true })
})
