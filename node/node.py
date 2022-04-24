
class Node:
    def __init__(
        self,
        host: str,
        seed_node_address_list: list(str)
    ):
        self.host = host
        self.seed_node_address_list = seed_node_address_list

    def initialize_known_nodes(self):
        # Initialize known nodes list from seed_node_address_list
        pass

    def advertise_to_seed_nodes(self):
        # Advertise itself to seed nodes so that those nodes
        # have this node in their known nodes list
        pass

    def advertise_to_know_nodes(self):
        # Advertise itself to known nodes so that those nodes have this node in their known node list
        pass
