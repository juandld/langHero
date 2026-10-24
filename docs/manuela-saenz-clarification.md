# Clarification needed: "Manuela's Science" (orchestrator task `7379a6766367426d`)

Status: **blocked on David's answer**. Do not invent story content — per David's own
instruction, any new story must be based on real source material, not fabricated.

## 1. The request, verbatim

From orchestrator queue item `b5dc3f5c07f64264` ("Spanish language immersion for entire
game"), auto-captured from voice note in session `7a4230ad-c308-4171-8f0b-396fd17b3847`
(audio: `/voice-notes/vn_1792863258349_ad64755e.m4a`):

> Okay, my favorite is Manuela's Science, and by the way, the whole game should be
> narrated and played in Spanish for the best language learning opportunity and
> immersion. So maybe there could be different levels to play based on your previous
> knowledge, and the vocabulary will change but the story will stay the same. It should
> follow her story from real life, but the multiple choice option should change the
> direction.

The clarify task itself, `7379a6766367426d` ("Clarify: who/what is 'Manuela's Science'
for the Spanish-immersion story?"), target project `langHero`, status `in_progress`,
confirms the same gap: Spanish-immersion *infrastructure* is shipped, but there is no
"Manuela" story to localize yet.

## 2. Evidence gathered

**No Manuela content exists anywhere in the two relevant repos:**

```
$ grep -ril manuela /home/claude-user/projects/langHero
(no matches)

$ grep -ril manuela /home/claude-user/projects/orchestratorHero
storage/orchestrator_queue.sqlite                                   # just this task's text
storage/progress/supervisor_runs/20261024_175556__7379a6766367426d.log
storage/progress/supervisor_runs/20261024_173539__b5dc3f5c07f64264.log
```

The only hits are the queue DB and supervisor run logs for these two tasks — i.e.
nothing to localize into a new story.

**Spanish-immersion infrastructure is real and shipped:**

- `backend/story/localize.py` — localization pipeline (exists, 7014 bytes)
- `frontend/src/lib/components/game/GameMenu.svelte` — has language / narration / 
  vocabulary-level selectors (exists, 12008 bytes)

**The original voice note/audio is not recoverable on this VPS** to re-listen for
context on what "my favorite" was chosen *from* — `~/.llm-terminal/voice-notes/` and
`~/.llm-terminal/messages*` have no file or record matching session `7a4230ad` or the
audio filename `vn_1792863258349_ad64755e.m4a`.

## 3. Hypothesis (not confirmed — do not build on this without David's sign-off)

"Manuela's Science" is most likely a speech-to-text mis-transcription of **Manuela
Sáenz** ("SAH-ens" in Spanish pronunciation can land close to "Science" in ASR output),
the Ecuadorian revolutionary known as the "**Libertadora del Libertador**"
("Liberatrice of the Liberator"):

- Born Quito, 27 Dec 1797; met Simón Bolívar in Quito in 1822; his companion until his
  death in 1830.
- On the night of 25 September 1828, she helped Bolívar escape an assassination attempt
  at the Palacio de San Carlos in **Bogotá** — the city David is currently based in
  (Chapinero).
- Exiled after Bolívar's death by Francisco de Paula Santander; lived out her life in
  Paita, Perú; died 1856.
- Sources: [Manuela Sáenz — Wikipedia](https://en.wikipedia.org/wiki/Manuela_S%C3%A1enz),
  [Septembrine Conspiracy — Wikipedia](https://en.wikipedia.org/wiki/Septembrine_Conspiracy),
  [Manuela Sáenz: the Liberator's saviour](https://mathewlyons.co.uk/2020/09/29/manuela-saenz-simon-bolivar-mistress-saviour/).

This fits every detail in the transcript: a real person ("follow her story from real
life"), a dramatic real event with branch points ("the multiple choice option should
change the direction" — e.g. does she warn him in time, how does the escape play out),
and geographic resonance with David's current location. But this is a guess, not a
confirmed identity, and the "my favorite" phrasing implies she was chosen from a list
David had in mind that isn't recorded anywhere accessible here.

## 4. Questions for David

1. **Identity**: Is "Manuela's Science" → **Manuela Sáenz**? Or a different Manuela, or
   something else entirely (a mis-transcription of a different word/name)? Also: what
   list was "my favorite" chosen from — is there a doc or prior conversation with
   candidate figures/stories that didn't make it into this VPS?
2. **Source material**: If it is Manuela Sáenz (or confirmed otherwise), what should the
   story be based on? Options to approve/choose from — no new content will be written
   until one is picked:
   - The Wikipedia article (EN and/or ES) on Manuela Sáenz, as a general reference.
   - A specific biography or article David has in mind.
   - David's own notes, if any exist outside this VPS.

## 5. Next step once answered

Once David confirms identity + source material, build the branching story via the
existing manifest-based panel generator (`story.manifest` + 
`panels_test.build_manifest_prompt` — see [[feedback_use_manifest_generator]] memory;
never bypass this, it's what keeps character reference images consistent), then run it
through `backend/story/localize.py` to produce the Spanish narration/levels using the
selectors already in `GameMenu.svelte`.

Related orchestrator items: `7379a6766367426d` (this clarify task, `in_progress`),
`b5dc3f5c07f64264` (blocked on cost ceiling — leave untouched).
