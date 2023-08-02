

class OmniInferAccountError(Exception):
    messages: str

    def __init__(self, m: str):
        self.messages = m

    def __str__(self):
        return self.messages

