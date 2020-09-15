"""
General purpose functions that are used in different places."
"""

def slicer(iterable, length):
    """Slices an iterable into object into length sized chunks."""
    full_length = len(iterable)
    part_length = (full_length // length)
    for i in range(part_length):
        yield iterable[i * length: i * length + length]


def str2bytes(data):
    """
    Converts a str with a bytes sequence into said sequence. If the given
    sequence is not even-sized, the last character is ignored.

    :param data: string with a byte-sequence in it (example: "ffd8")
    :returns: bytes object of that sequence (example: b"\\xff\\xd8")
    """
    return bytes.fromhex(data)
