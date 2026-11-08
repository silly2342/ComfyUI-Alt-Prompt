import re
import node_helpers

from .lora_curve import LoraHookLoad, LoraHookAlternate, LoraHooksApply

# [from:to:when]  from until `when`, then to      e.g. [cat:dog:0.5]
# [to:when]       nothing until `when`, then to    e.g. [dog:0.5]
# [from::when]    from until `when`, then nothing  e.g. [cat::0.5]
# `when` < 1 is a fraction of the sampled steps, >= 1 is an exact step number.
SWITCH = re.compile(r"\[([^\[\]:|]*)(?::([^\[\]:|]*))?:(\d+(?:\.\d+)?)\]")
# [a|b|c] alternation, cycles by step
ALT = re.compile(r"\[([^\[\]]*\|[^\[\]]*)\]")


# <from:to:when>  same as [from:to:when], but may contain other brackets, e.g. <cat:[a|b]:0.5>
# <to:when> and <from::when> work too. Nesting <> inside <> is fine.
ANGLE = re.compile(r"<([^<>]*)>")
NUMBER = re.compile(r"^\d+(?:\.\d+)?$")
_OPEN, _CLOSE = "\x00", "\x01"      # protects <...> that is not a switch command


def _split_top(s):
    """Split on ':' but not inside [ ] brackets."""
    parts, cur, depth = [], [], 0
    for ch in s:
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth = max(0, depth - 1)
        if ch == ":" and depth == 0:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    parts.append("".join(cur))
    return parts


def _resolve_angle(text, step, total):
    def sw(m):
        parts = _split_top(m.group(1))
        if len(parts) in (2, 3) and NUMBER.match(parts[-1].strip()):
            when = float(parts[-1])
            a, b = ("", parts[0]) if len(parts) == 2 else (parts[0], parts[1])
            switch_step = when * total if when < 1 else when
            return a if step < switch_step else b
        return _OPEN + m.group(1) + _CLOSE    # not a command, leave it alone

    while True:                                # innermost first, until nothing left
        new = ANGLE.sub(sw, text)
        if new == text:
            return text
        text = new


def resolve(text, step, total):
    def sw(m):
        a, b, when = m.group(1), m.group(2), float(m.group(3))
        if b is None:                      # [to:when]
            a, b = "", a
        switch_step = when * total if when < 1 else when
        return a if step < switch_step else b

    text = _resolve_angle(text, step, total)
    text = SWITCH.sub(sw, text)
    text = ALT.sub(
        lambda m: (lambda opts: opts[step % len(opts)])(m.group(1).split("|")),
        text,
    )
    return text.replace(_OPEN, "<").replace(_CLOSE, ">")


def sigma_to_percent(ms, sigma):
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
        n = len(sigmas) - 1
        sig = [float(s) for s in sigmas]

        bounds = (
            [0.0]
            + [sigma_to_percent(ms, (sig[i - 1] + sig[i]) / 2) for i in range(1, n)]
            + [1.0]
        )

        cache, out = {}, []
        for i in range(n):
            prompt = resolve(text, i, n)
            if prompt not in cache:
                cache[prompt] = clip.encode_from_tokens_scheduled(clip.tokenize(prompt))
            for cond in cache[prompt]:
                out += node_helpers.conditioning_set_values(
                    [cond],
                    {"start_percent": bounds[i], "end_percent": bounds[i + 1]},
                )
        return (out,)


NODE_CLASS_MAPPINGS = {
    "AltPromptEncode": AltPromptEncode,
    "LoraHookLoad": LoraHookLoad,
    "LoraHookAlternate": LoraHookAlternate,
    "LoraHooksApply": LoraHooksApply,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "AltPromptEncode": "Alt Prompt Encode (A1111 style)",
    "LoraHookLoad": "LoRA Hook Load (curve)",
    "LoraHookAlternate": "LoRA Hook Alternate (on/off by step)",
    "LoraHooksApply": "LoRA Hooks Apply",
}
