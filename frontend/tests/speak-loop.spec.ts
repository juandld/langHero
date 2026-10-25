import { expect, test } from '@playwright/test';

/**
 * End-to-end gameplay loop test.
 *
 * This drives the FULL path a learner takes:
 *   1. Navigate to a story
 *   2. Advance until a time-freeze speaking panel appears
 *   3. Click "Release Time & Speak" (which starts recording)
 *   4. Fake microphone (via Chrome --use-file-for-fake-audio-capture) feeds a
 *      canned WAV through getUserMedia → MediaRecorder
 *   5. MediaRecorder emits chunks → streamingManager sends them over the
 *      /stream/interaction WebSocket to the real backend
 *   6. Backend transcribes + runs process_interaction + emits event:final
 *   7. Frontend onFinal callback fires + SpeakResultCard renders
 *
 * The autoloop stretch's test suites all mocked the mic / scoring and so
 * missed the real-world bugs (invisible button, nothing-happens-on-record,
 * scenario-mode scoreDelta being dropped). This test exercises the whole
 * chain so that class of failure is caught.
 *
 * See docs/testing-strategy.md for the full research + remaining targets.
 */

test.describe('Gameplay loop — speak flow', () => {
  test('Release Time & Speak drives mic→ws→score→UI end to end', async ({ page }) => {
    test.setTimeout(60000);

    // Collect console errors so the test fails loud on any client-side break
    // (missing mic permission, websocket URL wrong, dropped exception).
    const errors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') errors.push(msg.text());
    });

    // Fresh state (no resumed save)
    await page.addInitScript(() => {
      try { localStorage.clear(); } catch { /* noop */ }
    });

    await page.goto('/play/story/shogun_test');
    await expect(page).toHaveTitle(/The Weight of Words/);

    // Advance panels until the time-freeze overlay renders a Release button.
    const releaseBtn = page.getByRole('button', { name: /Release Time & Speak/i });
    let advanced = 0;
    for (let i = 0; i < 25; i++) {
      if (await releaseBtn.count()) break;
      await page.keyboard.press('ArrowRight');
      advanced++;
      await page.waitForTimeout(600);
    }
    await expect(releaseBtn, `No Release Time & Speak button found after ${advanced} advances`).toBeVisible();

    // Verify the button is actually in the viewport — this is the exact
    // regression that slipped past the earlier autoloop (button at rect.top
    // 999 on a 768-high viewport = 231px below the fold).
    const vp = page.viewportSize();
    const box = await releaseBtn.boundingBox();
    expect(box, 'Release button has a bounding box').not.toBeNull();
    expect(box!.y, 'Release button top edge is on-screen').toBeGreaterThanOrEqual(0);
    expect(box!.y + box!.height, 'Release button bottom edge is on-screen').toBeLessThanOrEqual(vp!.height);

    // Click Release Time & Speak — starts recording. UI should swap button
    // label to "Stop & Submit" or similar.
    await releaseBtn.click();
    const stopBtn = page.getByRole('button', { name: /Stop & Submit|Stop Speaking/i });
    await expect(stopBtn, 'Recording started → stop button visible').toBeVisible({ timeout: 5000 });

    // Let the fake-audio stream for a couple of seconds so chunks reach the
    // backend. The WAV is ~18s long; 3s is plenty for process_interaction.
    await page.waitForTimeout(3000);

    // Submit — triggers mediaRecorder.stop() + streamingManager.signalStop
    await stopBtn.click();

    // The result card is the one unambiguous UI signal that the final event
    // arrived AND the frontend's onFinal handler fired. If this times out,
    // the websocket→final chain is broken (same bug class as #2135/#2136 or
    // streaming_interaction_test "penalty instead of final").
    const resultCard = page.locator('[data-testid="speak-result"]');
    await expect(resultCard, 'SpeakResultCard renders after final event').toBeVisible({ timeout: 15000 });

    // Loud-fail on JavaScript errors during the loop. Filter out:
    //  - microphone-permission messages (expected with Chrome fake-audio)
    //  - 404s for resources (cache misses or stale image refs — these don't
    //    break the gameplay loop and are tracked separately)
    const realErrors = errors.filter((e) =>
      !/microphone/i.test(e) &&
      !/Failed to load resource.*404/i.test(e) &&
      !/net::ERR_/i.test(e)
    );
    expect(realErrors, `JS errors during the speak loop: ${realErrors.join(' | ')}`).toEqual([]);
  });
});
