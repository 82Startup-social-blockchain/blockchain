from typing import Optional


class Account:
    def __init__(
        self,
        private_key: Optional[str] = None
    ):
        if private_key is None:
            # generate private_key
            pass
        else:
            self.private_key = private_key
