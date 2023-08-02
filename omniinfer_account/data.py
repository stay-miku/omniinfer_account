from dataclasses import dataclass
from typing import List


@dataclass
class txt2img:
    prompt: str = "cute little girl standing in a Mediterranean port town street,wind,pale-blonde hair, blue eyes,very long twintails,white dress,white hat,blue sky,laugh,double tooth,closed eyes,looking at viewer,lens flare,dramatic, coastal"
    model_name: str = "cuteyukimixAdorable_neochapter2_92321.safetensors"
    negative_prompt: str = "NG_DeepNegative_V1_75T, EasyNegativeV2,  extra fingers, fewer fingers, lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry, (worst quality, low quality:1.4), Negative2, (low quality, worst quality:1.4), (bad anatomy), (inaccurate limb:1.2), bad composition, inaccurate eyes, extra digit,fewer digits, (extra arms:1.2), (bad-artist:0.6), bad-image-v2-39000"
    sampler_name: str = "Euler a"
    batch_size: int = 1
    n_iter: int = 1
    steps: int = 20
    cfg_scale: int = 7
    seed: int = -1
    height: int = 512
    width: int = 512
    restore_faces: bool = False
    clip_skip: int = 2
    using_controlnet: bool = False
    controlnet_model: str = "control_v11p_sd15_openpose"
    controlnet_module: str = "none"
    controlnet_weight: float = 1.0
    controlnet_input_image: str = ""
    control_mode: int = 0
    controlnet_mask: int = -1
    controlnet_resize_mode: int = 1
    controlnet_lowvram: bool = False
    controlnet_processor_res: int = 64
    controlnet_threshold_a: int = 64
    controlnet_threshold_b: int = 64
    controlnet_guidance_start: float = 0.0
    controlnet_guidance_end: float = 1.0
    controlnet_pixel_perfect: bool = False

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        setattr(self, key, value)


@dataclass
class img2img:
    init_image: str = ""
    prompt: str = "cute little girl standing in a Mediterranean port town street,wind,pale-blonde hair, blue eyes,very long twintails,white dress,white hat,blue sky,laugh,double tooth,closed eyes,looking at viewer,lens flare,dramatic, coastal"
    model_name: str = "cuteyukimixAdorable_neochapter2_92321.safetensors"
    negative_prompt: str = "NG_DeepNegative_V1_75T, EasyNegativeV2,  extra fingers, fewer fingers, lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry, (worst quality, low quality:1.4), Negative2, (low quality, worst quality:1.4), (bad anatomy), (inaccurate limb:1.2), bad composition, inaccurate eyes, extra digit,fewer digits, (extra arms:1.2), (bad-artist:0.6), bad-image-v2-39000"
    sampler_name: str = "Euler a"
    batch_size: int = 1
    n_iter: int = 1
    steps: int = 20
    cfg_scale: int = 7
    seed: int = -1
    height: int = 512
    width: int = 512
    denoising_strength: float = 0.75
    restore_faces: bool = False
    clip_skip: int = 2

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        setattr(self, key, value)

