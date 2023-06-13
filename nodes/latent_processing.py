import torch

class LatentLerp:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "A": ("LATENT",),
                "B": ("LATENT",),
                "t": ("FLOAT", {"default": 0.5, "min": 0.0, "max": 1.0, "step": 0.01}),
            }
        }

    RETURN_TYPES = ("LATENT",)
    FUNCTION = "lerp_latent"

    CATEGORY = "latent"

    def lerp_latent(self, A, B, t):
        a = A.copy()
        b = B.copy()

        torch.lerp(a["samples"], b["samples"], t, out=a["samples"])

        return (a,)