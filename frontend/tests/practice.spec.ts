import { expect, test } from '@playwright/test';

// E2E for /practice v1c (live conversation with Jev feedback bar).
// Skipped until the route lands (queue item langhero-practice/frontend).

test.describe('/practice', () => {
  test('page loads with chat input + feedback bar', async ({ page }) => {
    const resp = await page.goto('/practice');
    test.skip(resp?.status() === 404, '/practice not implemented yet');

    await expect(page.getByTestId('practice-chat-input')).toBeVisible();
    await expect(page.getByTestId('practice-feedback-bar')).toBeVisible();

    // Four dimensions visible.
    for (const dim of ['grammatical', 'natural', 'register', 'meaning']) {
      await expect(page.getByTestId(`practice-bar-${dim}`)).toBeVisible();
    }
  });

  test('sending a message renders learner turn + eventual scores', async ({ page }) => {
    const resp = await page.goto('/practice');
    test.skip(resp?.status() === 404, '/practice not implemented yet');

    const input = page.getByTestId('practice-chat-input');
    await input.click();
    await input.fill('来一瓶啤酒');
    await page.getByTestId('practice-chat-send').click();

    // Learner message appears immediately.
    await expect(page.getByText('来一瓶啤酒')).toBeVisible();

    // Scores update within 5s (Jev p95 ≈ 2s + LLM turn stream).
    await expect(page.getByTestId('practice-bar-natural')).toHaveAttribute(
      'data-score',
      /^0?\.\d+$/,
      { timeout: 5000 },
    );
  });
});
