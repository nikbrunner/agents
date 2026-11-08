---
name: nbr-images
description: Generate or edit images with FLUX through the Black Forest Labs MCP, such as covers, artwork, wallpapers and illustrations. Use when Nik wants an image made, changed or restyled.
compatibility: The FLUX MCP (https://mcp.bfl.ai).
---

# Images

Images are made with FLUX through the `FLUX` MCP. The MCP calls the models; this skill is how we use them. A repo with its own image skill adds its subjects and where files go, on top of this one.

Read [references/flux.md](references/flux.md) before writing a prompt: the models and their costs, the wording that works, edits, filters and the traps.

## Prompt

Write one short block per job: the subject, the medium and look, then the scene with its light and framing. Keep the subject and medium blocks word for word across a series, and write the scene fresh for each image. Name each reference's job in the prompt ("Image 1 sets the palette, image 2 the composition").

## References

- **One job per reference, cropped to it.** A full image passes on everything in it: background, light, props. Crops of the same size weigh the same.
- **Each round passes the reference set.** The previous result stays out, because a chain of results drifts further every round.
- **One medium per image.** A drawing among the references of a photoreal image turns it into CG, and a photo of an object in an ink drawing comes out pasted in. Make the object in the target medium first.
- **Describe real people in words.** Their face and body seep into the result, so photos Nik shows to point at a pose or a build stay out of every upload.

## Making

An image works its way up in resolution, and Nik picks at every step:

1. **Draft** with `flux3_image` at `"768sq"`, one or two takes of each idea. A draft is the image at low resolution. Klein knows nothing of the subject or medium and draws its own generic look, so skip it for drafts.
2. **Finish** the draft Nik picks natively at `"4k"`. FLUX draws the detail at that size; an upscaler can only guess it.
3. **Edit** for small changes.
4. **Grade** locally: saturation and grain.

A color or palette version is a generation request, steered with the prompt or an edit and hex codes. Local steps stay limited to crop, resize, upscale and that grade. When the model can't steer a color, tell Nik and leave that version out.

## Keeping

1. **Save** every render as WebP (`cwebp -q 90 -m 6`). Outside a repo with its own rule, files go to `~/Pictures/agents/<job>/`, numbered in the order Nik should look at them.
2. **Record the chain** of every image built in more than one step in a sidecar `.md` beside it: each step in order with its model, resolution, references by file name and the full prompt. FLUX purges its history after about two hours, so write it while the session still holds the prompts.

Look at each result before showing Nik, and say plainly what landed and what didn't.
