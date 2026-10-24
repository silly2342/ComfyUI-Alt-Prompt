# ComfyUI-Alt-Prompt

A1111-style alternating and switching prompts for ComfyUI. Works with any model
that uses the standard sampler timestep ranges (including DiT models like MOSS-Image).

## Install
Put the `ComfyUI-Alt-Prompt` folder in `ComfyUI/custom_nodes/` and restart.
The node is **Alt Prompt Encode (A1111 style)** in the `conditioning` category.

## Alternation (changes every step)
- `[a|b]`    a, b, a, b ...
- `[a||]`    a, empty, empty, a, empty, empty ...
- `[a|||b]`  a, empty, empty, b, a ...
- Any number of pipes works: options cycle by `step % number_of_options`.

## Switching (changes once, at a point in time)
- `[a:b:0.5]`  a for the first half of the steps, then b
- `[b:0.3]`    nothing until 30% of the way through, then b
- `[a::0.5]`   a for the first half, then nothing
- `when` below 1 is a fraction of the sampled steps; 1 or above is an exact step number.

Both can be combined in one prompt. Brackets without a `|` or a trailing
number (e.g. JSON boxes like [10,20,100,100]) are left alone.
Nesting one bracket inside another is not supported.

## Wiring
Feed the SAME sigmas (from BasicScheduler or similar) into both this node and
SamplerCustomAdvanced. If you change denoise, change it on the scheduler.
Inputs: clip, model, sigmas, text. Output: conditioning.

## Notes
- Each unique resolved prompt is encoded once, so this is cheap.
- Step numbering and the switch fraction both refer to the steps actually sampled,
  so with denoise 0.65 the "0.5" point is halfway through that shorter run.
- Empty slots are encoded as an empty string, not removed.
