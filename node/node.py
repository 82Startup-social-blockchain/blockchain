from typing import List
import json
import requests

from utils import constants


class Node:
    def __init__(
        self,
        address: str
    ):
        self.address = address
        self.known_node_address_set = self._initialize_known_node_address_set()

    def _initialize_known_node_address_set(self):
        # TODO: use something better than just json

        # Initialize known nodes list from seed_node_address_list
        with open(constants.SEED_NODES_FILE, 'r') as fp:
            address_set = set(json.load(fp))
        return address_set

    def _request_addresses_from_known_nodes(self):
        # Request node addresses from known nodes
        added_address_set = set([])
        disconnected_address_set = set([])
        for address in self.known_node_address_set:
            if address == self.address:
                continue
            url = address + constants.KNOWN_NODES_PATH
            try:
                r = requests.get(url=url)
                added_address_set.update(set(r.json()))
            except requests.exceptions.ConnectionError:
                disconnected_address_set.add(address)

        self.known_node_address_set.update(added_address_set)
        self.known_node_address_set.discard(self.address)
        self.known_node_address_set.difference_update(disconnected_address_set)

    def _advertise_to_known_nodes(self):
        # Advertise itself to known nodes so that those nodes have this node in their known node list
        disconnected_address_set = set([])
        for address in self.known_node_address_set:
            if address == self.address:
                continue
            url = address + constants.NODE_REQUEST_PATH
            data = {"address": self.address}
            headers = {"Content-Type": "application/json"}
            try:
                requests.post(url=url, json=data, headers=headers)
            except requests.exceptions.ConnectionError:
                disconnected_address_set.add(address)

        self.known_node_address_set.difference_update(disconnected_address_set)

    def join_network(self):
        # 1. Ask seed nodes for their known nodes
        self._request_addresses_from_known_nodes()

        # 2. Advertise itself to known nodes
        self._advertise_to_known_nodes()

        print("known_node_address_set: ", self.known_node_address_set)

        # 3. get blockchain from known nodes
        pass

    def accept_new_node(self, address):
        self.known_node_address_set.add(address)
        print("updated known node address: ", self.known_node_address_set)
