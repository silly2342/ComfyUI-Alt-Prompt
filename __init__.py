# Drop this folder into ComfyUI/custom_nodes/alt_prompt/ and restart ComfyUI.
#
# Syntax (A1111 style):
#   [a|b]     alternate a, b, a, b ... every step
#   [a||]     a, empty, empty, a, empty, empty ...
#   [a|b|c]   cycles by step % len
#
# Only brackets that contain a pipe are treated as alternation, so JSON arrays
# like [10,20,100,100] are left alone (just don't put a "|" inside them).

import re
import node_helpers

ALT = re.compile(r"\[([^\[\]]*\|[^\[\]]*)\]")


def resolve(text, step):
    return ALT.sub(
        lambda m: (lambda opts: opts[step % len(opts)])(m.group(1).split("|")),
        text,
    )


def sigma_to_percent(ms, sigma):
    # percent_to_sigma is monotonically decreasing, so bisect
    lo, hi = 0.0, 1.0
    for _ in range(40):
        mid = (lo + hi) / 2
        if ms.percent_to_sigma(mid) > sigma:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


class AltPromptEncode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "clip": ("CLIP",),
                "model": ("MODEL",),
                "sigmas": ("SIGMAS",),
                "text": ("STRING", {"multiline": True, "dynamicPrompts": False}),
            }
        }

    RETURN_TYPES = ("CONDITIONING",)
    FUNCTION = "encode"
    CATEGORY = "conditioning"

    def encode(self, clip, model, sigmas, text):
        ms = model.get_model_object("model_sampling")
        n = len(sigmas) - 1  # number of steps
        sig = [float(s) for s in sigmas]

        # step boundaries as percents, split at midpoints between neighbouring sigmas
        bounds = (
            [0.0]
            + [sigma_to_percent(ms, (sig[i - 1] + sig[i]) / 2) for i in range(1, n)]
            + [1.0]
        )

        cache, out = {}, []
        for i in range(n):
            prompt = resolve(text, i)
            if prompt not in cache:  # encode each unique prompt only once
                cache[prompt] = clip.encode_from_tokens_scheduled(clip.tokenize(prompt))
            for cond in cache[prompt]:
                out += node_helpers.conditioning_set_values(
                    [cond],
                    {"start_percent": bounds[i], "end_percent": bounds[i + 1]},
                )
        return (out,)


NODE_CLASS_MAPPINGS = {"AltPromptEncode": AltPromptEncode}
NODE_DISPLAY_NAME_MAPPINGS = {"AltPromptEncode": "Alt Prompt Encode (A1111 style)"}
