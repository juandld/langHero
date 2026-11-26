<script>
  import LegalPage from '$lib/components/LegalPage.svelte';
</script>

<LegalPage title="Pricing">
  <p class="note">Draft plans, pending David's approval (decision 8A). Nothing can be bought yet.</p>

  <table>
    <thead>
      <tr><th></th><th>Free</th><th>Trial (once per account)</th><th>Plus</th></tr>
    </thead>
    <tbody>
      <tr>
        <th>Price</th>
        <td>$0</td>
        <td>$0, no card</td>
        <td><mark class="ph">[price]</mark> (proposed: $12/mo or $96/yr)</td>
      </tr>
      <tr>
        <th>Play bundled and published stories, with audio and grading</th>
        <td>Unlimited</td>
        <td>Unlimited</td>
        <td>Unlimited</td>
      </tr>
      <tr>
        <th>Import or generate your own stories</th>
        <td>0</td>
        <td>1 story (video up to 5 min)</td>
        <td>8 stories per month, at most 2 a day</td>
      </tr>
      <tr>
        <th>Video import minutes per story</th>
        <td>–</td>
        <td>5</td>
        <td>20</td>
      </tr>
      <tr>
        <th>Live streaming tutor</th>
        <td>5 min/day</td>
        <td>15 min/day for 7 days</td>
        <td>20 min/day</td>
      </tr>
      <tr>
        <th>Illustrated panels per generated story</th>
        <td>–</td>
        <td>6</td>
        <td>6</td>
      </tr>
      <tr>
        <th>Saves and history</th>
        <td>Cloud saves</td>
        <td>Cloud saves</td>
        <td>Cloud saves and a private library of your own stories</td>
      </tr>
      <tr>
        <th>Publish your own story</th>
        <td>–</td>
        <td>Yes, with rights confirmation</td>
        <td>Yes, with rights confirmation</td>
      </tr>
    </tbody>
  </table>

  <p>
    Payments are processed by Paddle, our reseller and merchant of record, which adds VAT or sales tax where it applies.
    Cancel anytime; see the <a href="/refund">14-day refund policy</a>.
  </p>
</LegalPage>

<style>
  .note {
    font-weight: 600;
  }
</style>
