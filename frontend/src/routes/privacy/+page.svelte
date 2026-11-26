<script>
  import LegalPage from '$lib/components/LegalPage.svelte';
</script>

<LegalPage title="Privacy Policy">
  <h2>1. Controller</h2>
  <p>
    The data controller is <mark class="ph">[legal entity]</mark>, <mark class="ph">[address]</mark>, Iceland. Contact for
    privacy questions and requests: <mark class="ph">[contact email]</mark>. We process personal data under the GDPR, as
    applied in the EEA.
  </p>

  <h2>2. What we collect and why</h2>
  <table>
    <thead>
      <tr><th>Data</th><th>Purpose</th><th>Legal basis</th></tr>
    </thead>
    <tbody>
      <tr>
        <td>Email address (magic-link sign-in, when accounts are enabled)</td>
        <td>Your account, quotas, receipts and service messages</td>
        <td>Contract</td>
      </tr>
      <tr>
        <td>Saves, progress and your own stories</td>
        <td>Keeping your learning history and library</td>
        <td>Contract</td>
      </tr>
      <tr>
        <td>Voice recordings and their transcripts</td>
        <td>Transcribing and grading your spoken answers, and the live tutor</td>
        <td>Contract</td>
      </tr>
      <tr>
        <td>Content you import (video, text, links)</td>
        <td>Turning it into lessons for you</td>
        <td>Contract</td>
      </tr>
      <tr>
        <td>Payment details</td>
        <td>Collected and held by Paddle, not by us. We receive the order status and your email.</td>
        <td>Contract</td>
      </tr>
      <tr>
        <td>Technical logs (IP address, request times)</td>
        <td>Security and abuse prevention</td>
        <td>Legitimate interest</td>
      </tr>
    </tbody>
  </table>

  <h2>3. Processors we share data with</h2>
  <ul>
    <li><strong>OpenAI</strong>: speech transcription and answer grading.</li>
    <li><strong>Google Gemini</strong>: story generation, images and the live tutor.</li>
    <li><strong>ElevenLabs</strong>: text-to-speech audio.</li>
    <li><strong>typesafe.ai (Jev)</strong>: answer grading, via its hosted API.</li>
    <li><strong>Appwrite</strong>: email sign-in and accounts, when accounts are enabled.</li>
    <li><strong>Paddle</strong>: payments, as merchant of record.</li>
    <li><strong>Cloudflare</strong>: hosting network, access control and content delivery.</li>
  </ul>
  <p>
    Some of these processors are outside the EEA. Where that applies, transfers rely on the EU Standard Contractual
    Clauses or an adequacy decision.
  </p>

  <h2>4. How long we keep data</h2>
  <p>
    Streaming voice and transcripts: <mark class="ph">[retention rule D6]</mark>. Account data, saves and stories are kept
    while your account exists and deleted when you delete your account. Paddle keeps payment records as tax law requires.
  </p>

  <h2>5. Your rights</h2>
  <p>Under the GDPR you have the right to:</p>
  <ul>
    <li>access the personal data we hold about you;</li>
    <li>have it corrected (rectification);</li>
    <li>have it deleted (erasure);</li>
    <li>restrict how we process it;</li>
    <li>receive it in a portable format (portability);</li>
    <li>object to processing based on legitimate interest.</li>
  </ul>
  <p>
    Email <mark class="ph">[contact email]</mark> to use any of these rights. You can also complain to a supervisory
    authority; in Iceland that is Persónuvernd (<a href="https://www.personuvernd.is" target="_blank"
      rel="noopener noreferrer">personuvernd.is</a>), or the authority where you live.
  </p>

  <h2>6. No sale of data</h2>
  <p>We do not sell your personal data and do not use it for advertising.</p>
</LegalPage>
