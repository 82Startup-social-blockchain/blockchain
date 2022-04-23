import enum


class TransactionType(enum.Enum):
    POST = 1
    COMMENT = 2
    REPLY = 3
    SHARE = 4
    REACT_LIKE = 5
    REPORT = 6

    # TODO: add more react types, report?, make it a token? (co-ownership)


class TransactionContentType(enum.Enum):
    NONE = 0  # if the content does not require content upload
    STRING = 1
    HTML = 2
