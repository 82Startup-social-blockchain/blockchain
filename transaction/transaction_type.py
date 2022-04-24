import enum


class TransactionType(enum.IntEnum):
    POST = 1
    EDIT_POST = 2
    DELETE_POST = 3
    COMMENT = 4
    EDIT_COMMENT = 5
    DELETE_COMMENT = 6
    REPLY = 7
    EDIT_REPLY = 8
    DELETE_REPLY = 9
    SHARE = 10
    REACT_LIKE = 11
    REPORT = 12
    TIP = 13
    FOLLOW = 14
    UNFOLLOW = 15

    # TODO: add more react types, report?, make it a token? (co-ownership)


class TransactionContentType(enum.IntEnum):
    NONE = 0  # if the content does not require content upload
    STRING = 1
    HTML = 2
