import { expect, test } from '@playwright/test'

test('operator console runs workflow and records reconciliation', async ({ page }) => {
  await page.goto('/')

  await expect(page.getByRole('heading', { name: /supervised ai decision workflows/i })).toBeVisible()

  await page.screenshot({ path: 'test-artifacts/01-initial-console.png', fullPage: true })

  await page.getByRole('button', { name: 'Initialize Run' }).click()
  await expect(page.getByText(/determine whether the stripe role is worth pursuing/i)).toBeVisible()

  await page.getByRole('button', { name: 'Run All' }).click()

  await expect(page.getByText(/Generated structured decision artifact/i)).toBeVisible()
  await expect(page.getByText(/scope: full/i)).toBeVisible()
  await expect(page.getByText(/conditionally_pursue|pursue/i)).toBeVisible()

  await page.screenshot({ path: 'test-artifacts/02-post-run-console.png', fullPage: true })

  const operatorControls = page.getByTestId('operator-controls-panel')

  await page.getByRole('button', { name: 'Apply Feedback' }).click()
  await expect(operatorControls.locator('.stacked-list .list-item strong').first()).toHaveText('force_retrieval')

  await page.getByRole('button', { name: 'Re-run' }).click()
  await expect(page.getByText(/scope: full/i)).toBeVisible()

  await page.screenshot({ path: 'test-artifacts/03-post-feedback-console.png', fullPage: true })
})
