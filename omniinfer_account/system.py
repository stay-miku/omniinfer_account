import omniifer_api

from .account import account
from .error import OmniInferAccountError
from typing import Dict, List
import logging
import os
import time
import threading
import json
from . import config


class system:
    task_list: List[List]
    account_list: Dict[str, account]
    stop: bool
    update_stop: bool
    path: str

    # start system, auto start task resolve thread, read account data by path
    def __init__(self, path):
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.task_list = []
        self.account_list = {}
        self.stop = False
        self.update_stop = False
        if not os.path.exists(path):
            os.makedirs(path)
        self.path = path
        files = os.listdir(path)
        logging.info("Init: Reading accounts' data...")
        i = 0
        for file in files:
            if file.endswith(".json"):
                i += 1
                self.account_list[file.split(".")[0]] = account(os.path.join(path, file))
        logging.info("Init: Read {} account data".format(str(i)))
        resolve = threading.Thread(target=self.task_resolve)
        resolve.start()
        omniifer_api.update()
        update = threading.Thread(target=self.updating)
        update.start()

    # stop system, stop child thread and save data in path
    def stopping(self):
        # stop task
        self.stop = True
        self.update_stop = True
        logging.info("System: Waiting the task resolver and updater stop...")
        while self.stop:
            time.sleep(0.1)
        while self.update_stop:
            time.sleep(0.1)
        logging.info("System: Saving the accounts' data...")
        for key in self.account_list:
            self.account_list[key].save(os.path.join(self.path, key + ".json"))
        logging.info("System: Stopped")

    def updating(self):
        logging.info("Update: start update")
        i = 0
        while not self.update_stop:
            time.sleep(1)
            i += 1
            if i >= config.update_interval:
                logging.info("Update: update")
                omniifer_api.update()
                logging.info("Update: backup account data")
                for key in self.account_list:
                    self.account_list[key].save(os.path.join(self.path, key + ".json"))
                i = 0
        logging.info("Update: stop")
        self.update_stop = False

    # resolve task thread, auto start after __init__, auto stop before stopping
    def task_resolve(self):
        logging.info("Task: Started task resolve")
        while not self.stop:
            if len(self.task_list) == 0:
                time.sleep(1)
                continue
            task = self.task_list[0]
            logging.info("Task: Process task: {} {}".format(task[0], task[1]))
            try:
                self.account_list[task[0]].status = 2
                self.task_list.pop()
                if task[1] == "t2i":
                    task_id = self.account_list[task[0]].txt2img()
                elif task[1] == "i2i":
                    task_id = self.account_list[task[0]].img2img()
                elif task[1] == "upscale":
                    task_id = self.account_list[task[0]]\
                        .upscale(task[2]["image"], task[2]["resize"], task[2]["upscaler"])
                else:
                    raise OmniInferAccountError("Unknown task mode: {}".format(task[1]))
                logging.info("Task: {} task_id {}".format(task[0], task_id))
                logging.info("Task: waiting generate...")
                while 1:
                    time.sleep(1)
                    result = omniifer_api.progress(task_id
                                                   , self.account_list[task[0]].self_api_key if self
                                                   .account_list[task[0]].using_self_api_key else "")
                    if result["status"] == 2 or result["status"] == 3 or result["status"] == 4:
                        self.account_list[task[0]].status = 0
                        self.account_list[task[0]].last_result = result
                        logging.info("Task: task resolved")
                        break
                    else:
                        self.account_list[task[0]].last_result = result
                        logging.info("Task: progress: {}".format(str(result["progress"])))

            except KeyError:
                logging.info("Task: Account not found: {}".format(task[0]))
                continue
            except OmniInferAccountError as e:
                logging.warning("Task: Image generates failed: {} by {}".format(str(e), task[0]))
                self.account_list[task[0]].last_result = {"status": 3, "failed reason": str(e)}
                self.account_list[task[0]].status = 0
                continue
            except omniifer_api.OMNI_INFER_API_ERROR as e:
                logging.warning("Task: Image generates failed: {} by {}".format(str(e), task[0]))
                self.account_list[task[0]].last_result = {"status": 3, "failed reason": "API error"}
                self.account_list[task[0]].status = 0
                continue
            except Exception as e:
                logging.error("Task: " + str(e) + " by {}".format(task[0]))
                self.account_list[task[0]].status = 0
                self.account_list[task[0]].last_result = {"status": 3, "failed reason": "UnException Error"}
                continue

        self.stop = False
        logging.info("Task: stop")

    # system api    need account status = 0
    def add_task(self, account_id: int, mode: str) -> Dict:
        try:
            if mode != "t2i" and mode != "i2i":
                logging.warning("AddTask: Unknown mode " + mode)
                return {"code": 1, "msg": "Unknown mode {}".format(mode)}
            if self.account_list[str(account_id)].status != 0:
                logging.warning("AddTask: {} is already in the queue".format(str(account_id)))
                return {"code": 1, "msg": "There are already task in the queue"}
            self.account_list[str(account_id)].status = 1
            self.task_list.append([str(account_id), mode])
            logging.info("AddTask: {} add task".format(str(account_id)))
            return {"code": 0, "msg": "Currently ranked {} in the task queue".format(str(len(self.task_list)))}

        except KeyError:
            logging.warning("AddTask: " + "Unknown account id {}".format(str(account_id)))
            return {"code": 1, "msg": "Unknown account id {}".format(str(account_id))}

    def add_upscale_task(self, account_id: int, image: str, resize: float, upscaler="R-ESRGAN 4x+"):
        try:
            if self.account_list[str(account_id)].status != 0:
                logging.warning("AddTask: {} is already in the queue".format(str(account_id)))
                return {"code": 1, "msg": "There are already task in the queue"}
            self.account_list[str(account_id)].status = 1
            self.task_list.append([str(account_id), "upscale", {"image": image, "resize": resize, "upscaler": upscaler}])
            logging.info("AddUpscaleTask: {} add task".format(str(account_id)))
            return {"code": 0, "msg": "Currently ranked {} in the task queue".format(str(len(self.task_list)))}

        except KeyError:
            logging.warning("AddUpscaleTask: " + "Unknown account id {}".format(str(account_id)))
            return {"code": 1, "msg": "Unknown account id {}".format(str(account_id))}

    # code 0: complete, 1: error, 2: waiting, 3, processing
    def get_result(self, account_id: int):
        try:
            result = self.account_list[str(account_id)].last_result
            if self.account_list[str(account_id)].status == 0:
                self.account_list[str(account_id)].last_result = {}
                if result is None:
                    return {"code": 1, "msg": "No task"}
                if result["status"] == 2:
                    try:
                        return {"code": 0, "msg": "", "imgs": result["imgs"], "seed": json.loads(result["info"])["seed"]
                                , "time": result["debug_info"]["submit_time_ms"] - result["debug_info"]["finish_time_ms"]}
                    except json.JSONDecodeError:
                        return {"code": 0, "msg": "", "imgs": result["imgs"],
                                "time": result["debug_info"]["submit_time_ms"] - result["debug_info"]["finish_time_ms"]}
                elif result["status"] == 3 or result["status"] == 4:
                    return {"code": 1, "msg": result["failed reason"]}
                else:
                    return {"code": 1, "msg": "UnException status"}
            elif self.account_list[str(account_id)].status == 1:
                return {"code": 2, "msg": "Waiting in queue."}
            elif self.account_list[str(account_id)].status == 2:
                return {"code": 3, "msg": "", "progress": result["progress"] if result != {} else 0.0}

        except KeyError:
            logging.warning("GetResult: Unknown account {}".format(str(account_id)))
            return {"code": 1, "msg": "Unknown account id"}

    def create_account(self, account_id: int):
        if str(account_id) in self.account_list:
            logging.warning("CreateAccount: {} already exists".format(str(account_id)))
            return {"code": 1, "msg": "account already exists"}
        self.account_list[str(account_id)] = account(account_id)
        logging.info("CreateAccount: {} created".format(str(account_id)))
        return {"code": 0, "msg": ""}

    def set(self, account_id: int, mode: str, key: str, value):
        try:
            self.account_list[str(account_id)].set(mode, key, value)
            if key != "init_image" and key != "controlnet_input_image":
                logging.info("Set: {} set {}.{} as {}".format(str(account_id), mode, key, str(value)))
            else:
                logging.info("Set: {} set {}.{}".format(str(account_id), mode, key))
            return {"code": 0, "msg": ""}
        except KeyError:
            logging.warning("Set: Unknown account id {}".format(str(account_id)))
            return {"code": 1, "msg": "Unknown account id {}".format(str(account_id))}
        except OmniInferAccountError as e:
            logging.warning("Set: {}".format(str(e)))
            return {"code": 1, "msg": str(e)}

    def set_person_api_key(self, account_id: int, api_key: str):
        try:
            self.account_list[str(account_id)].set_person_api_key(api_key)
            return {"code": 0, "msg": ""}
        except KeyError:
            logging.warning("SetKey: Unknown account {}".format(str(account_id)))
            return {"code": 1, "msg": "Unknown account id"}
        except OmniInferAccountError as e:
            logging.warning("SetKey: {}".format(str(e)))
            return {"code": 1, "msg": str(e)}

    def get(self, account_id: int, mode: str, key: str):
        try:
            if mode == "t2i":
                return {"code": 0, "msg": "", "value": str(self.account_list[str(account_id)].t2i_data[key])}
            elif mode == "i2i":
                return {"code": 0, "msg": "", "value": str(self.account_list[str(account_id)].i2i_data[key])}
            else:
                return {"code": 1, "msg": "Unknown mode"}
        except KeyError:
            logging.warning("Get: Unknown account {}".format(str(account_id)))
            return {"code": 1, "msg": "Unknown account id"}
        except TypeError:
            return {"code": 1, "msg": "Unknown key {}".format(key)}

    def put_model(self, model_version_id: int):
        try:
            omniifer_api.put_model(model_version_id)
            return {"code": 0, "msg": ""}
        except omniifer_api.OMNI_INFER_API_ERROR as e:
            logging.warning("Put: {}".format(str(e)))
            return {"code": 1, "msg": "API error"}

    def search_model(self, keyword):
        try:
            r = omniifer_api.search_models(keyword)
            result = []
            for i in r:
                result.append({
                    "name": i["name"],
                    "sd_name": i["sd_name"],
                    "type": i["type"],
                    "version_id": i["civitai_version_id"]
                })
            return {"code": 0, "msg": "", "result": result}
        except omniifer_api.OMNI_INFER_API_ERROR as e:
            logging.warning("Search: {}".format(str(e)))
            return {"code": 1, "msg": "API error"}
        except Exception as e:
            logging.error("Search: " + str(e))
            return {"code": 1, "msg": "Internal Error"}

    def model_enable(self, model_version_id):
        try:
            r = omniifer_api.check_model_available(model_version_id)
            return {"code": 0, "msg": "", "enable": r}
        except omniifer_api.OMNI_INFER_API_ERROR as e:
            logging.warning("Enable: {}".format(str(e)))
            return {"code": 1, "msg": str(e)}
        # except Exception as e:
        #     logging.error("Enable: " + str(e))
        #     return {"code": 1, "msg": "Internal Error"}

    def get_info(self, account_id: int):
        try:
            return {
                "code": 0,
                "msg": "",
                "id": self.account_list[str(account_id)].id,
                "remain_credit": self.account_list[str(account_id)].remain_credit,
                "used_credit": self.account_list[str(account_id)].used_credit,
                "self_api_key": self.account_list[str(account_id)].self_api_key
            }
        except KeyError:
            logging.warning("GetInfo: Unknown account {}".format(str(account_id)))
            return {"code": 1, "msg": "Unknown account id"}

    def set_model_name_by_version_id(self, account_id: int, mode: str, version_id: int):
        try:
            sd_name = self.account_list[str(account_id)].set_model_by_version(mode, version_id)
            logging.info("SetById: set {} {} model name as {}".format(str(account_id), mode, sd_name))
            return {"code": 0, "msg": "", "sd_name": sd_name}
        except KeyError:
            logging.warning("SetById: Unknown account {}".format(str(account_id)))
            return {"code": 1, "msg": "Unknown account id"}
        except OmniInferAccountError as e:
            logging.warning("SetById: " + str(e))
            return {"code": 1, "msg": str(e)}

    def set_credit(self, account_id: int, credit: int):
        try:
            self.account_list[str(account_id)].remain_credit = credit
            return {"code": 0, "msg": ""}
        except KeyError:
            logging.warning("SetC: Unknown account {}".format(str(account_id)))
            return {"code": 1, "msg": "Unknown account id"}

    def add_credit(self, account_id: int, credit: int):
        try:
            self.account_list[str(account_id)].remain_credit += credit
            return {"code": 0, "msg": ""}
        except KeyError:
            logging.warning("AddC: Unknown account {}".format(str(account_id)))
            return {"code": 1, "msg": "Unknown account id"}

    def add_prompt(self, account_id: int, mode: str, prompt: str):
        try:
            self.account_list[str(account_id)].add_prompt(mode, prompt)
            return {"code": 0, "msg": ""}
        except KeyError:
            logging.warning("AddP: Unknown account {}".format(str(account_id)))
            return {"code": 1, "msg": "Unknown account id"}
        except OmniInferAccountError as e:
            logging.warning("AddP: " + str(e))
            return {"code": 1, "msg": str(e)}

    def add_negative_prompt(self, account_id: int, mode: str, prompt: str):
        try:
            self.account_list[str(account_id)].add_negative_prompt(mode, prompt)
            return {"code": 0, "msg": ""}
        except KeyError:
            logging.warning("AddN: Unknown account {}".format(str(account_id)))
            return {"code": 1, "msg": "Unknown account id"}
        except OmniInferAccountError as e:
            logging.warning("AddN: " + str(e))
            return {"code": 1, "msg": str(e)}
