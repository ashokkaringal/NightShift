import { expect, test } from '@playwright/test'
import { openApp, openListItem, selectSidebarFilter } from './helpers'

test.describe('NightShift UI regressions', () => {
  test('safety banner and sidebar counts load', async ({ page }) => {
    await openApp(page)

    await expect(page.getByRole('button', { name: /^Inbox\s+5$/ })).toBeVisible()
    await expect(page.getByRole('button', { name: /^Staged drafts\s+3$/ })).toBeVisible()
    await expect(page.getByRole('button', { name: /^Urgent \(RED\)\s+3$/ })).toBeVisible()
    await expect(page.getByRole('button', { name: /^Follow-up \(YELLOW\)\s+1$/ })).toBeVisible()
    await expect(page.getByRole('button', { name: /^Approved\s+1$/ })).toBeVisible()
    await expect(page.getByRole('button', { name: /^Rejected\s+1$/ })).toBeVisible()
  })

  test('approved RED draft shows APPROVED badge, not NO REPLY', async ({ page }) => {
    await openApp(page)
    await selectSidebarFilter(page, /^Approved/)

    await expect(page.getByText('email-001')).toBeVisible()
    await expect(page.getByText('APPROVED', { exact: true })).toBeVisible()
    await expect(page.getByText('NO REPLY', { exact: true })).not.toBeVisible()
    await expect(
      page.getByText('Manager sign-off recorded — outbound send is still blocked in v1'),
    ).toBeVisible()
  })

  test('YELLOW staged draft shows HITL action buttons', async ({ page }) => {
    await openApp(page)
    await selectSidebarFilter(page, /Follow-up \(YELLOW\)/)

    await expect(page.getByText('email-006')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Approve draft' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Reject', exact: true })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Snooze', exact: true })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Save edits' })).toBeVisible()
  })

  test('GREEN staged draft shows NO REPLY chip', async ({ page }) => {
    await openApp(page)
    await selectSidebarFilter(page, /^Staged drafts/)

    await openListItem(page, /Hallway lightbulb out/)
    await expect(page.getByText('email-002')).toBeVisible()
    await expect(page.getByText('NO REPLY', { exact: true })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Approve draft' })).not.toBeVisible()
    await expect(
      page.getByText('GREEN priority — logged for records only', { exact: false }),
    ).toBeVisible()
  })

  test('rejected draft shows rejection footer', async ({ page }) => {
    await openApp(page)
    await selectSidebarFilter(page, /^Rejected/)

    await expect(page.getByText('email-003')).toBeVisible()
    await expect(
      page.getByText('Rejected — this draft will not be sent.'),
    ).toBeVisible()
  })

  test('sidebar filter switch replaces stale detail pane', async ({ page }) => {
    await openApp(page)
    await selectSidebarFilter(page, /Follow-up \(YELLOW\)/)

    await expect(page.getByText('email-006')).toBeVisible()
    await expect(page.getByText('email-001')).not.toBeVisible()

    await selectSidebarFilter(page, /^Rejected/)

    await expect(page.getByText('email-003')).toBeVisible()
    await expect(page.getByText('email-006')).not.toBeVisible()
    await expect(
      page.getByText('Rejected — this draft will not be sent.'),
    ).toBeVisible()
  })

  test('reject staged draft keeps detail pane in sync', async ({ page }) => {
    await openApp(page)
    await selectSidebarFilter(page, /Follow-up \(YELLOW\)/)

    await expect(page.getByText('email-006')).toBeVisible()
    await expect(page.getByText('STAGED', { exact: true })).toBeVisible()

    const rejectReady = page.waitForResponse(
      (resp) => resp.url().includes('/reject') && resp.ok(),
    )
    await page.getByRole('button', { name: 'Reject', exact: true }).click()
    await rejectReady

    await expect(page.getByText('email-006')).toBeVisible()
    await expect(
      page.getByText('Rejected — this draft will not be sent.'),
    ).toBeVisible()
    await expect(page.getByRole('button', { name: 'Approve draft' })).not.toBeVisible()
  })

  test('approve action transitions staged RED draft to APPROVED', async ({ page }) => {
    await openApp(page)
    await selectSidebarFilter(page, /Urgent \(RED\)/)

    await openListItem(page, /City code violation notice/)
    await expect(page.getByText('email-007')).toBeVisible()
    await expect(page.getByText('STAGED', { exact: true })).toBeVisible()

    const approveReady = page.waitForResponse(
      (resp) => resp.url().includes('/approve') && resp.ok(),
    )
    await page.getByRole('button', { name: 'Approve draft' }).click()
    await approveReady

    await expect(page.getByText('APPROVED', { exact: true })).toBeVisible()
    await expect(page.getByText('NO REPLY', { exact: true })).not.toBeVisible()
    await expect(page.getByText('Approved by Maria Santos', { exact: false })).toBeVisible()
  })
})
