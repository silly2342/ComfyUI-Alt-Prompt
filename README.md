# ComfyUI-Alt-Prompt

A1111-style alternating prompts for ComfyUI. Works with any model that uses
the standard sampler timestep ranges (including DiT models like MOSS-Image).

## Install
Put the `ComfyUI-Alt-Prompt` folder in `ComfyUI/custom_nodes/` and restart.
The node is **Alt Prompt Encode (A1111 style)** in the `conditioning` category.

## Syntax
- `[a|b]`    a, b, a, b ... every step
- `[a||]`    a, empty, empty, a, empty, empty ...
- `[a|||b]`  a, empty, empty, b, a ...
- Any number of pipes works: options cycle by `step % number_of_options`.
- Brackets without a `|` (e.g. JSON boxes like [10,20,100,100]) are left alone.

## Wiring
Feed the SAME sigmas (from BasicScheduler or similar) into both this node and
SamplerCustomAdvanced. If you change denoise, change it on the scheduler.
Inputs: clip, model, sigmas, text. Output: conditioning.

## Notes
- Each unique resolved prompt is encoded once, so alternating is cheap.
- Step numbering restarts at 0 on every sampler pass (e.g. a second denoise pass).
- Empty alternation slots are encoded as an empty string, not removed.
