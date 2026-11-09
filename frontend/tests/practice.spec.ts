import { expect, test } from '@playwright/test';

// E2E for /practice v1c (live conversation with Jev feedback bar).
// Skipped until the route lands (queue item langhero-practice/frontend).

// /practice no longer auto-picks the first scenario — user must choose
// explicitly from the scenario-menu first. Both tests now pick a scenario
// via the first available menu card before asserting the chat UI.
async function pickFirstScenario(page: import('@playwright/test').Page) {
  await page.getByTestId('practice-scenario-menu').waitFor();
  // scenario-menu renders one card per scenario; click the first available.
  // Must scope to button[data-testid^=...] — the plain attribute selector
  // also matches the menu container's own "practice-scenario-menu" testid
  // (same prefix), and .first() would grab that no-op div instead of a card
  // whenever the click races ahead of the scenarios fetch populating cards.
  await page.locator('button[data-testid^="practice-scenario-"]').first().click();
}

test.describe('/practice', () => {
  test('page loads with chat input + feedback bar', async ({ page }) => {
    const resp = await page.goto('/practice');
    test.skip(resp?.status() === 404, '/practice not implemented yet');
    await pickFirstScenario(page);

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
    await pickFirstScenario(page);

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

  test('mic button records and fills the chat input via transcription', async ({ page }) => {
    const resp = await page.goto('/practice');
    test.skip(resp?.status() === 404, '/practice not implemented yet');
    await pickFirstScenario(page);

    const input = page.getByTestId('practice-chat-input');
    await expect(input).toHaveValue('');

    const micButton = page.getByTestId('practice-mic-button');
    await micButton.click();
    await expect(micButton).toHaveClass(/recording/);

    // Let the fake audio device feed a couple seconds of audio before stopping.
    await page.waitForTimeout(1500);
    await micButton.click();
    await expect(micButton).not.toHaveClass(/recording/);

    // Transcription round-trip fills the textarea (fake capture + real STT backend).
    await expect(input).not.toHaveValue('', { timeout: 15000 });
  });
});
