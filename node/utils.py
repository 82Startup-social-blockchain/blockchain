from typing import Dict

from account.account import Account


def get_stakes_from_accounts(account_dict: Dict[bytes, Account]) -> Dict[bytes, int]:
    account_stake_dict = dict()
    for public_key_hex in account_dict:
        if account_dict[public_key_hex].stake > 0:
            account_stake_dict[public_key_hex] = account_dict[public_key_hex].stake

    return account_stake_dict
