
from block.validator_rand import ValidatorRand


class ValidatorRandError(Exception):
    def __init__(self, validator_rand: ValidatorRand, message=""):
        base_message = f"(validator: {validator_rand.validator_public_key_hex})"
        error_message = f"{message} {base_message}"
        super().__init__(error_message)


class ValidatorRandSignatureError(Exception):
    def __init__(self, validator_rand, message=""):
        super().__init__(validator_rand, message=f"[ValidatorRandSignatureError] {message}")


class ValidatorRandValueError(Exception):
    def __init__(self, validator_rand, message=""):
        super().__init__(validator_rand, message=f"[ValidatorRandValueError] {message}")
