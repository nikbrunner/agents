# FLUX

How to prompt FLUX (Black Forest Labs) through the `FLUX` MCP: the models,
the wording that works, and the traps. Built from BFL's FLUX 3 guides (see
Sources) and from our own sessions.

## Models

| Model               | Use                                                                                                                 | Cost                                   |
| ------------------- | ------------------------------------------------------------------------------------------------------------------- | -------------------------------------- |
| `flux3_image`       | Everything by default: drafts, keepers, edits. Up to 10 references, sized by `aspect_ratio` + `resolution`, no seed | `768sq` 4.1, `1k` 4.8, `2k` 10 credits |
| `flux2_klein_4b`    | Pose sketches                                                                                                       | 1.4 credits                            |
| `flux2_pro_preview` | Outpainting (see Editing), fixed `seed`                                                                             | about 12 credits at 3.4 MP             |
| `flux2_max`         | Looks most like a real frame, loses proportions and costume                                                         | 16 credits                             |

FLUX.2 models size by `width` × `height`, at most 4 MP in total.

## The prompt

BFL's order, as sentences: the medium and look, the subject and what it
does, the setting, the light, the framing. Put first whatever matters most.

- **Open with one sentence that sets the medium and look**, concretely:
  "Color night photograph with the heavy grain of 35 mm film shot at ISO
  3200". A camera, lens or film stock plus what it does to the image
  ("visible grain", "a warm color cast") says more than "cinematic" or
  "professional". Keep light out of this sentence: "photographed under soft
  daylight" there lights the whole frame flat.
- **Write only what is visible.** Every phrase names something you could point
  to in the frame. Mood words ("quiet, grieving, very still", "calm") do
  nothing, and quality tags ("masterpiece", "highly detailed") add nothing.
- **Say what is there, not what is absent.** FLUX has no negative prompt.
  Write "the back of her head toward the viewer" for "face not visible", and
  "the paper around the figure is blank" for "no text anywhere".
- **Literal words land literally.** "Eyes half closed, listening" closes her
  eyes. Name the eyes, the gaze and the hands as they should look: "her dark
  brown eyes open, looking down at the candles".
- **Similes land as objects.** "Hugs the sheet like a teddy bear" draws a
  toy. Describe the pose instead.
- **Length follows the control you need.** FLUX 3 expands the prompt itself.
  Several subjects, a layout or text take more sentences; cut any sentence
  that describes nothing visible.
- **References by position, the same words each time,** each with a role:
  subject, product, setting or style. "Image 1 supplies her face, image 2 the
  blades, image 3 the skin." The base image goes first: with `aspect_ratio`
  on auto, the output takes its shape. "Only" does not hold: a build
  reference in a leotard puts a leotard strap under a jumper. When the outfit
  differs, write the build in words instead.
- **Leave out a reference the frame does not show.** A face reference pulls a
  back view around to the front. For a back view, pass the hair crop and
  nothing else from the head.

## Positions

Plain words first ("in the lower right of the frame"). Where a position must
hold, add one row per element after the caption and cite its id in the
caption as `<id>`:

```text
A tall woman <figure_1> lies on her side facing the viewer ...

{"id": "figure_1", "bbox": [480, 150, 820, 850], "desc": "the whole reclining woman, both arms and both hands included"}
```

`bbox` is `[top, left, bottom, right]` on a 0 to 1000 grid per axis, and
`desc` describes appearance. Boxes guide the composition and do not clip, so a
prohibition in a row does nothing. Set `aspect_ratio` to the one the boxes
were drawn for. FLUX 3 has no separate JSON scene mode; these rows are the
structure.

## Light

Name one source, its direction and quality, what it lights, and what falls
into shadow. Labels like "dim", "low-key", "moody" or "underexposed" barely
move FLUX; it lights rooms brighter than asked. BFL's own example: "a small
candle that provides a warm orange point of light".

- Candle scene: "Five small candles on the floor provide the only light,
  warm orange points that light her face, hands and knees; the walls and the
  room behind her stay black."
- Chiaroscuro needs a named source: "single practical desk lamp, strong
  chiaroscuro lighting". The bare word lights the room evenly.
- Other terms that work: "practical lighting" (lamps, neon, fire visible in
  the frame), "rim light", "split lighting".
- Overcast, window and soft daylight read as flat and even; they do not make
  a dark room.
- A light named in the scene gets switched on. A fluorescent tube "above the
  mirror" lights the whole frame flat even when the prompt calls the room
  dark. Leave out lights that should be off.
- One unified palette reads as film: "the only color is magenta and teal
  neon against near-black". Mixed warm and cold sources clash.

## Grain and grade

- **Grain:** name it as an effect with a cause: "visible grain", "35 mm film
  shot at ISO 3200" (BFL lists ISO 1600–3200 as the grainy look). Fresh
  renders draw it thin all the same. An edit that adds it ("Add heavy,
  coarse, clearly visible 35 mm film grain over the whole frame, strongest in
  the shadows") works reliably.
- **Local grade** for the last step, free and without drift:
  - saturation: `magick in.png -modulate 100,60 out.png` (60% is Nik's pick
    for the film look)
  - grain: `magick in.png \( +clone -fill gray50 -colorize 100 -attenuate 0.45 +noise Gaussian -colorspace gray -blur 0x0.6 \) -compose overlay -composite out.png`
  - Darkness is not a grade. A global curve (`-level`, gamma) crushes the
    shadows into flat, cheap-looking patches. Get darkness from the render or
    from an edit that relights the scene.

## Resolution

A face that takes up only a few dozen pixels comes out smeared: eyes, a
watch, small objects. Wide shots with a small figure go natively to `2k`. An
edit of a `1k` draft up to `2k` only enlarges the smear. `768sq` is for
testing wording, not for judging faces.

`flux3_image` renders up to `4k` (about 16 MP) at about six times the cost of
`2k`. A finished image goes there natively instead of through an upscaler.
When an upscale is the only way, run the model on the image at its native
size and scale down afterwards:
`upscayl-bin -n high-fidelity-4x -s 4`, then `magick -filter Lanczos -resize`.
Resizing first softens the grain the model then smooths. `digital-art-4x`
turns skin to plastic; `ultrasharp-4x` adds crackle to skin.

## Medium and surface

Wording moves the composition, not a medium's surface. White lines on black
paper drift toward scratchboard however the skin is described. A swatch made
in the target material (a shoulder in blended white charcoal) passed as a
reference ("image N sets only the skin: the medium, the blending and the
shading, nothing of its figure") changes the surface. Make the swatch
without references, so nothing of an older surface comes along.

## Wording traps

| Words                                                        | What FLUX makes                                                  | Write instead                                                                                                                                                              |
| ------------------------------------------------------------ | ---------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| "bodysuit", "catsuit", "second skin"                         | a leotard with bare legs, or a jacket over trousers              | "a matte black full-length wetsuit, one single piece from her neck down to her ankles, no seam at the waist"                                                               |
| "armor", "plates"                                            | a superhero kit                                                  | the protection as part of the fabric, unless the kit is wanted                                                                                                             |
| "plain, soft boots"                                          | slippers                                                         | the boots by look: "tall armored boots to just below the knee, overlapping shin plates"                                                                                    |
| "naked" (even "a naked bike")                                | blocked by the input filter                                      | the object by its parts                                                                                                                                                    |
| "eyes half closed"                                           | eyes shut                                                        | open eyes and a named gaze                                                                                                                                                 |
| "the body of a professional MMA fighter"                     | real muscle, but a man's chest and arms on her                   | a woman's build named as such ("a female heptathlete's build") plus a build reference                                                                                      |
| "lean", "slim", "athletic" alone                             | a dancer                                                         | the build in muscles and a female sport, or a build reference                                                                                                              |
| "heavily muscled"                                            | mass, not definition                                             | the look of the muscle: "lean, defined build of a female CrossFit athlete: low body fat, round capped shoulders, a narrow waist on wide hips, thighs with a visible sweep" |
| a small object held to the head ("a watch to her ear")       | the object fused to her as jewelry, or a second one on her wrist | the object set down in the scene, the hands at rest                                                                                                                        |
| "hugs the sheet like a teddy bear"                           | a toy                                                            | "her arms wrapped around the folded sheet, pulling it to her chest"                                                                                                        |
| "her face turned away and not visible" with a hair reference | a faceless wig                                                   | "the back of her head toward the viewer, the bob falling over her shoulder"                                                                                                |
| "back to viewer, facing the window" in one clause            | a twisted torso, an extra hand                                   | the body and the head in separate clauses: "her back to the viewer, her head turned left toward the window"                                                                |
| "no text anywhere", "nothing outside this box"               | nothing documented                                               | "the paper around the figure is blank"; drop the box clause                                                                                                                |

## Editing

- Form: "Modify image 1 by replacing … with … Keep the rest of the image
  exactly unchanged, preserving …". Name the target so only one thing
  matches ("her left arm, the one that hangs down by the sink").
- Change in a scene with a mirror: say "on her body and in the mirror
  reflection", or only one of them changes.
- An edit keeps the source's crop, resolution and look; a change of medium,
  scale or framing needs a new image. Each round drifts a little (often
  brighter and warmer), so stack few edits.
- An edit can fix what a fresh render keeps getting wrong: a light switched
  off, grain added, an outfit swapped, an arm matched to its reflection.
- **Outpainting** (zoom out): `flux2_pro_preview` with `width` × `height`
  larger than the source, at most 4 MP. Shrink a larger source first (a 2k
  frame to 2240×960, out to 2800×1200). It redraws the figure too, not only
  the new edges.
- Hex codes pin a color in an edit: "change only her hair to #d8a7b1".

## Filters

- Set `safety_tolerance` to 4, the highest `flux3_image` accepts (FLUX.2 goes
  to 6). At the default 2, skin-tight suits seen from behind or opened at the
  chest get blocked.
- Several body words in one prompt ("skin", "goosebumps", "opened to her
  stomach") can still trip the input filter at 4. The request fails as
  `moderated_input` and costs nothing. Say it plainer: "the zip pulled down
  to her navel, the suit's edges still covering her chest".

## Running

- Upload a reference with `request_upload_url`, then `curl -X PUT` the bytes
  with their content type; pass `{id: media_id}`. Ids stay valid for the
  session (20 images, oldest evicted first), so reuse them instead of
  uploading again.
- Submit one or two images per call, at most 8 running at once (more get
  `429 concurrency limit`). `503 over capacity` and `GENERATION_FAILED` go
  away on a plain retry.
- A `2k` render takes two to four minutes. Wait with a background `sleep`,
  then read `get_history(after=…, status="all")` for the result URL.
- Without a seed, two runs of one prompt differ: judge a wording change on
  two takes, not one.

## Sources

- [Building a Good Prompt](https://docs.bfl.ml/guides/prompting_unified_building)
- [Style, Aesthetics & Text](https://docs.bfl.ml/guides/prompting_unified_style)
- [Prompt Reference](https://docs.bfl.ml/guides/prompting_unified_reference)
- [Single-Reference Editing](https://docs.bfl.ml/guides/prompting_editing_single_reference)
- [Multi-Reference Editing](https://docs.bfl.ml/guides/prompting_editing_multi_reference)
- [Layout prompts](https://docs.bfl.ml/guides/prompting_layout)
- [Bounding boxes with FLUX 3 Image](https://docs.bfl.ml/flux_3/flux3_image_bounding_boxes)
