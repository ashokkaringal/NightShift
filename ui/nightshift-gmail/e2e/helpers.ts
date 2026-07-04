import { expect, type Page } from '@playwright/test'

export async function openApp(page: Page) {
  await page.goto('/')
  await expect(
    page.getByText('NightShift drafts. It never sends', { exact: false }),
  ).toBeVisible()
  await expect(page.getByRole('button', { name: /^Inbox\s+\d+$/ })).toBeVisible()
}

export async function selectSidebarFilter(page: Page, label: RegExp) {
  const inboxReady = page.waitForResponse(
    (resp) => resp.url().includes('inbox') && resp.ok(),
  )
  await page.getByRole('button', { name: label }).click()
  await inboxReady
}

export async function openListItem(page: Page, subject: RegExp | string) {
  const detailReady = page.waitForResponse(
    (resp) => resp.url().includes('/items/') && resp.ok(),
  )
  await page.getByText(subject).first().click()
  await detailReady
  await expect(page.getByText(/^email-/)).toBeVisible()
}
