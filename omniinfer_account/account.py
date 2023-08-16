import logging

import omniifer_api

from .data import txt2img, img2img
from . import config, error
import json
from typing import Dict


class account:
    id: int                 # unique verify  (use qq number need long in java)
    remain_credit: int      # used to generate image
    used_credit: int
    t2i_data: txt2img       # txt2img parameter
    i2i_data: img2img       # img2img parameter
    # 0: ready 1: waiting 2: processing    used to system task
    status: int
    # save the last result information, contain code fail_msg seed image's url ...  delete after inquiring
    last_result: Dict
    self_api_key: str
    using_self_api_key: bool

    def __init__(self, get):
        if isinstance(get, str):
            with open(get, "r", encoding="utf-8") as f:
                data = json.loads(f.read())

            self.id = data["id"]
            self.remain_credit = data["remain_credit"]
            self.used_credit = data["used_credit"]
            self.t2i_data = txt2img(**data["t2i_data"])
            self.i2i_data = img2img(**data["i2i_data"])
            self.status = 0
            self.last_result = {}
            self.self_api_key = data["self_api_key"]
            self.using_self_api_key = data["using_self_api_key"]

        elif isinstance(get, int):
            self.id = get
            self.remain_credit = config.default_credit
            self.used_credit = 0
            self.t2i_data = txt2img()
            self.i2i_data = img2img()
            self.status = 0
            self.last_result = {}
            self.self_api_key = ""
            self.using_self_api_key = False

        else:
            raise error.OmniInferAccountError("Bad type: " + str(type(get)))

    def save(self, file_name: str):
        data = {
            "id": self.id,
            "remain_credit": self.remain_credit,
            "used_credit": self.used_credit,
            "t2i_data": self.t2i_data.__dict__,
            "i2i_data": self.i2i_data.__dict__,
            "self_api_key": self.self_api_key,
            "using_self_api_key": self.using_self_api_key
        }

        with open(file_name, "w", encoding="utf-8") as f:
            f.write(json.dumps(data))

    def credit_calculate(self, c_type: str):
        if c_type == "t2i":
            height = self.t2i_data.height
            width = self.t2i_data.width
            n = self.t2i_data.n_iter
            batch = self.t2i_data.batch_size
        elif c_type == "i2i":
            height = self.i2i_data.height
            width = self.i2i_data.width
            n = self.i2i_data.n_iter
            batch = self.i2i_data.batch_size
        else:
            raise error.OmniInferAccountError("Error c_type: " + c_type)

        if width <= 512 and height <= 512:
            cost = 15
        elif width <= 768 and height <= 768:
            cost = 68
        elif width <= 1024 and height <= 1024:
            cost = 143
        elif width <= 2048 and height <= 2048:
            cost = 593
        else:
            raise error.OmniInferAccountError("Error size: height: {}, width: {}"
                                              .format(str(height), str(width)))

        return n * batch * cost

    # 检查并修改
    def set(self, mode: str, key: str, value):
        if (key == "prompt" or key == "model_name" or key == "sampler_name" or key == "controlnet_model"
            or key == "controlnet_module" or key == "controlnet_input_image" or key == "control" or key == "init_image") and (
                not isinstance(value, str) or value == ""):
            raise error.OmniInferAccountError("Key " + key + " is not str or be null")
        elif (key == "batch_size" or key == "n_iter") and (not isinstance(value, int) or not 1 <= value <= 8):
            raise error.OmniInferAccountError("Key " + key + " is not int or out of range")
        elif key == "steps" and (not isinstance(value, int) or not 1 <= value <= 50):
            raise error.OmniInferAccountError("Key steps is not int or out of range")
        elif key == "cfg_scale" and (not isinstance(value, int) or not 0 <= value <= 30):
            raise error.OmniInferAccountError("Key cfg_scale is not int or out of range")
        elif key == "seed" and (not isinstance(value, int) or not -1 <= value <= 2 ** 32):
            raise error.OmniInferAccountError("Key seed is not int or out of range")
        elif (key == "width" or key == "height") and (not isinstance(value, int) or not 1 <= value <= 2048
                                                      or not value % 8 == 0):
            raise error.OmniInferAccountError("Key " + key + " is not int or out of range")
        elif (key == "restore_faces" or key == "using_controlnet" or key == "controlnet_lowvram"
              or key == "controlnet_pixel_perfect") and not isinstance(value, bool):
            raise error.OmniInferAccountError("Key " + key + " is not bool")
        elif key == "clip_skip" and (not isinstance(value, int) or not 1 <= value):
            raise error.OmniInferAccountError("Key clip_skip is not int or out of range")
        elif key == "controlnet_weight" and (not isinstance(value, float) or not 0.0 <= value <= 2.0):
            raise error.OmniInferAccountError("Key controlnet_weight is not float or out of range")
        elif (value == "control_mode" or key == "controlnet_resize_mode") and (
                not isinstance(value, int) or not 0 <= value <= 2):
            raise error.OmniInferAccountError("Key " + key + "is not int or out of range")
        elif value == "controlnet_mask" and (not isinstance(value, int) or not value >= -1):
            raise error.OmniInferAccountError("Key controlnet_mask is not int or out of range")
        elif (
                key == "controlnet_processor_res" or key == "controlnet_threshold_a" or key == "controlnet_threshold_b") and not isinstance(
            value, int):
            raise error.OmniInferAccountError("Key " + key + " is not int")
        elif (key == "controlnet_guidance_start" or key == "controlnet_guidance_end") and not isinstance(value, float):
            raise error.OmniInferAccountError("Key " + key + " is not float")
        elif key == "denoising_strength" and (not isinstance(value, float) or not 0.0 <= value <= 1.0):
            raise error.OmniInferAccountError("Key denoising_strength is not float or out of range")

        # if key.startswith("control") and mode == "i2i":
        #     raise error.OmniInferAccountError("Key not found in i2i mode")
        #
        # if (key == "init_image" or key == "denoising_strength") and mode == "t2i":
        #     raise error.OmniInferAccountError("Key not found in t2i mode")

        if mode == "t2i":
            try:
                self.t2i_data[key] = value
            except TypeError:
                raise error.OmniInferAccountError("Key can not be found in t2i mode")
        elif mode == "i2i":
            try:
                self.i2i_data[key] = value
            except TypeError:
                raise error.OmniInferAccountError("Key can not be found in i2i mode")
        else:
            raise error.OmniInferAccountError("Unknown mode")

    def add_prompt(self, mode: str, value: str):
        if mode == "t2i":
            self.t2i_data.prompt += " " + value + ","
        elif mode == "i2i":
            self.i2i_data.prompt += " " + value + ","
        else:
            raise error.OmniInferAccountError("Unknown mode")

    def add_negative_prompt(self, mode: str, value: str):
        if mode == "t2i":
            self.t2i_data.negative_prompt += " " + value + ","
        elif mode == "i2i":
            self.i2i_data.negative_prompt += " " + value + ","
        else:
            raise error.OmniInferAccountError("Unknown mode")

    # only can be used by system.task_resolve
    def txt2img(self) -> str:
        # if self.status == 1:
        #     raise error.OmniInferAccountError("The last generate request is waiting")
        # elif self.status == 2:
        #     raise error.OmniInferAccountError("The last generate request is progressing")
        cost = self.credit_calculate("t2i")
        if not self.using_self_api_key:
            if self.remain_credit < cost:
                raise error.OmniInferAccountError("Not enough credits")

        if self.t2i_data.prompt == "":
            raise error.OmniInferAccountError("Prompt is empty")
        if self.t2i_data.using_controlnet:
            if self.t2i_data.controlnet_input_image == "":
                raise error.OmniInferAccountError("Input_image is required when using controlnet.")

        try:
            task_id = omniifer_api.txt2img(
                prompt=self.t2i_data.prompt,
                model_name=self.t2i_data.model_name,
                negative_prompt=self.t2i_data.negative_prompt,
                sampler_name=self.t2i_data.sampler_name,
                batch_size=self.t2i_data.batch_size,
                n_iter=self.t2i_data.n_iter,
                steps=self.t2i_data.steps,
                cfg_scale=self.t2i_data.cfg_scale,
                seed=self.t2i_data.seed,
                height=self.t2i_data.height,
                width=self.t2i_data.width,
                restore_faces=self.t2i_data.restore_faces,
                clip_skip=self.t2i_data.clip_skip,
                sd_vae=self.t2i_data.sd_vae,
                using_controlnet=self.t2i_data.using_controlnet,
                controlnet_model=self.t2i_data.controlnet_model,
                controlnet_module=self.t2i_data.controlnet_module,
                controlnet_weight=self.t2i_data.controlnet_weight,
                controlnet_input_image=self.t2i_data.controlnet_input_image,
                control_mode=self.t2i_data.control_mode,
                controlnet_mask=self.t2i_data.controlnet_mask,
                controlnet_resize_mode=self.t2i_data.controlnet_resize_mode,
                controlnet_lowvram=self.t2i_data.controlnet_lowvram,
                controlnet_processor_res=self.t2i_data.controlnet_processor_res,
                controlnet_threshold_a=self.t2i_data.controlnet_threshold_a,
                controlnet_threshold_b=self.t2i_data.controlnet_threshold_b,
                controlnet_guidance_start=self.t2i_data.controlnet_guidance_start,
                controlnet_guidance_end=self.t2i_data.controlnet_guidance_end,
                controlnet_pixel_perfect=self.t2i_data.controlnet_pixel_perfect,
                api_key=self.self_api_key if self.using_self_api_key else ""
            )
            if not self.using_self_api_key:
                self.remain_credit -= cost
                self.used_credit += cost
            return task_id
        except omniifer_api.OMNI_INFER_API_ERROR as e:
            logging.error(str(e))
            raise error.OmniInferAccountError("API error")

    def img2img(self) -> str:
        # if self.status == 1:
        #     raise error.OmniInferAccountError("The last generate request is waiting")
        # elif self.status == 2:
        #     raise error.OmniInferAccountError("The last generate request is progressing")

        cost = self.credit_calculate("i2i")
        if not self.using_self_api_key:
            if self.remain_credit < cost:
                raise error.OmniInferAccountError("Not enough credits")

        if self.i2i_data.init_image == "":
            raise error.OmniInferAccountError("Init_image is empty")

        try:
            task_id = omniifer_api.img2img(
                init_images=[self.i2i_data.init_image],
                prompt=self.i2i_data.prompt,
                model_name=self.i2i_data.model_name,
                negative_prompt=self.i2i_data.negative_prompt,
                sampler_name=self.i2i_data.sampler_name,
                batch_size=self.i2i_data.batch_size,
                n_iter=self.i2i_data.n_iter,
                steps=self.i2i_data.steps,
                cfg_scale=self.i2i_data.cfg_scale,
                seed=self.i2i_data.seed,
                height=self.i2i_data.height,
                width=self.i2i_data.width,
                denoising_strength=self.i2i_data.denoising_strength,
                restore_faces=self.i2i_data.restore_faces,
                clip_skip=self.i2i_data.clip_skip,
                sd_vae=self.i2i_data.sd_vae,
                api_key=self.self_api_key if self.using_self_api_key else ""
            )
            if not self.using_self_api_key:
                self.remain_credit -= cost
                self.used_credit += cost
            return task_id
        except omniifer_api.OMNI_INFER_API_ERROR as e:
            logging.error(str(e))
            raise error.OmniInferAccountError("API error")

    def set_person_api_key(self, api_key: str):
        if self.status != 0:
            raise error.OmniInferAccountError("While image generating, API key can not be changed.")
        if api_key == "":
            self.using_self_api_key = False
        else:
            self.using_self_api_key = True
        self.self_api_key = api_key

    def set_model_by_version(self, mode: str, version_id: int):
        try:
            model = omniifer_api.get_model(version_id)
            if model is None:
                raise error.OmniInferAccountError("Model not be put currently")
            if not model["enable"]:
                raise error.OmniInferAccountError("Model {} is not enabled currently".format(model["name"]))
            sd_name = model["sd_name"]
            if mode == "t2i":
                self.t2i_data.model_name = sd_name
            elif mode == "i2i":
                self.i2i_data.model_name = sd_name
            else:
                raise error.OmniInferAccountError("Error mode {}".format(mode))
            return sd_name
        except omniifer_api.OMNI_INFER_API_ERROR as e:
            logging.error("OMNI_INFER_API_ERROR: " + str(e))
            raise error.OmniInferAccountError(str(e))

    def upscale(self, image: str, resize: float, upscaler="R-ESRGAN 4x+"):
        data = omniifer_api.upscale_data(image=image, upscaling_resize=resize, upscaler_1=upscaler, api_key= self.self_api_key if self.using_self_api_key else -1)
        if image == "":
            raise error.OmniInferAccountError("Image can not be null")

        try:
            task_id = omniifer_api.upscale(data)
            return task_id

        except omniifer_api.OMNI_INFER_API_ERROR as e:
            logging.error(str(e))
            raise error.OmniInferAccountError("API error")


