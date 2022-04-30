import enum


class TransactionType(enum.IntEnum):
    POST = 1
    EDIT_POST = 2  # TODO: edit/delete must be performed by the creator
    DELETE_POST = 3
    COMMENT = 4
    EDIT_COMMENT = 5
    DELETE_COMMENT = 6
    REPLY = 7
    EDIT_REPLY = 8
    DELETE_REPLY = 9
    SHARE = 10
    REACT_LIKE = 11
    REPORT = 12  # have minimum fee
    TIP = 13
    FOLLOW = 14
    UNFOLLOW = 15
    TRANSFER = 16  # transfer some kind of identifier (e.g. web3 game item)
    STAKE = 17

    # TODO: add more react types, report?, make it a token? (co-ownership)


class TransactionContentType(enum.IntEnum):
    STRING = 1
    HTML = 2
