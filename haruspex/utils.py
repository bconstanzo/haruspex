"""
General purpose functions that are used in different places."
"""

def hexshow(data):
    """
    Pretty prints in the console the bytes object it takes as parameter.

    :param data: a bytes sequence to pretty print on the screent
    """
    lines = [data[i * 16: i * 16 + 16] for i in range(len(data) //16)]
    for i, line in enumerate(lines):
        out = f"{i * 16:08x} | "
        out += " ".join( f"{b:02x}" for b in line )
        out += " "
        out += "".join(
            f"{i}"
            for i in map(
                lambda x: chr(x) if chr(x) in string.printable else ".", line))
        print(out)

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
