from typing import List
import random


def stringToBinary(string:str)->str:
    """
    Converting String to binary.

    Parameter.
    ----------
    string : str
        String you want to convert to binary.
    """
    return ''.join(format(ord(i), '08b') for i in string)

def binarytoArrayBynary(binary:str)->List[int]:
    """
    Converting binary string to list of bytes integer.

    Parameter.
    ----------
    binary : str
        binary string you want to convert.

    """
    return [binary[i:i+8] for i in range(0, len(binary), 8)]

def ArrayBynarytoString(binary:List[int])->str:
    """
    Converting binary string  to string.

    Parameter.
    ----------
    binary : str
        binary string you want to convert.

    """
    # Search for file extension.
    string =""
    for object in (binary):
        string += chr(int(object,2))
    return string

def ByteToBinary(byte:bytes)->str:
    """
    Converting byte to binary.

    Parameter.
    ----------
    arrayByte : byteArray
        byteArray you want to convert to binary.
    """
    return ''.join(format(byte, "08b"))

def arrayByteToBinary(arrayByte:bytearray)->str:
    """
    Converting arraybite to binary.

    Parameter.
    ----------
    arrayByte : byteArray
        byteArray you want to convert to binary.
    """
    return ''.join([format(i, "08b") for i in arrayByte])

def modifyBit(value:int, position:int, bit:int) -> int:
    """
    Modify bit of specific integer "value" at position "position" with bit value "bit".

    Parameter.
    ----------
    value : int
        Value of integer that you want to modify it's bit.
    position : int
        Position of bit you want to change, LSB is position 0.
    bit: int
        The bit value.
    """
    mask = 1 << position
    return (value & ~mask) | ((bit << position) & mask)

def generate_random_access_table(key:str, length:int) -> List[int]:
    """
    Generate randomized access table using specified key for randomized lsb purpose.

    Parameter.
    ----------
    key : str
        key for seeding randomizer.
    length: int 
        length of table you want to generate.
    """
    # Initialize table of consecutive array
    random_access_table = list(range(1, length)) 

    # Seed the randomizer so it will return same random value with same key.
    random.seed(key)
    # Randomize and return the table.
    random.shuffle(random_access_table)
    return random_access_table
