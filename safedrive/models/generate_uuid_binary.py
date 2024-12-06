from uuid import uuid4


def generate_uuid_binary():
    """Generate a binary UUID."""
    return uuid4().bytes