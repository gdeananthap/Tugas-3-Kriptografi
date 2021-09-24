# Python module.
import os
import wave
import ntpath

from pathlib import Path

# Own module.
from helper import ArrayBynarytoString, ByteToBinary, binarytoArrayBynary, generate_random_access_table, modifyBit, stringToBinary, arrayByteToBinary

class AudioStegano:
    """
    A class used for representing Steganography with audio.

    Attributes.
    ----------

    """

    def __init__(self, audio_path:str, input_message_path:str=None) -> None:
        """
        Constructor for AudioStegano class. Read input audio file and input message file.
        Format for audio must be WAV, input message can be any file.

        Parameter.
        ----------
        audio_path : str
            Absolute path to audio file.
        input_message_path : str
            Absolute path to message file.
        """

        # Check audio file validity for processing.
        # Check extension.
        if (os.path.splitext(audio_path)[1].lower() != ".wav"):
            raise Exception("Can only process wav file for audio")
        # Check if file exist.
        audio = wave.open(audio_path, "r")
        if (not(audio)):
            raise Exception("Input audio not exist")

        # Process audio input.
        self.audio = audio
        self.audio_path = audio_path
        # Get audio bytes representation.
        audio_frames = self.audio.readframes(self.audio.getnframes())
        self.audio_bytes = bytearray(list(audio_frames))
        self.payload = len(audio_frames)

        # Process input messages.
        if (input_message_path):
            # Check if file exist.
            messages:bytes = open(input_message_path, "rb").read()
            if (not(messages)):
                raise Exception("Input message not exist")
            self.message = messages
            self.msg_extension = os.path.splitext(input_message_path)[1].lower()[1:]
            # Check if current audio file is big enough to hide text.
            # For each bytes(8 bit) you can only hide one bit from message. You also need to keep space 
            # for input file extension and randomized, encrypt, start and endfile flag. 
            if len(self.message) > self.payload//8 - len(self.msg_extension) - 5:
                raise Exception("Input message is to big")

    def normalizeMessage(self, key:str, is_random:bool, is_encrypt:bool) -> str:
        """
        Function to normalize message you want to encrypt by inserting specific flag and turn the 
        string to binary. 
        Return normalized message.

        Parameter.
        ----------
        is_random : bool, default false
            Boolean indicating lsb randomized or not.
        is_encrypt : bool, default false
            Boolean indicating message encrypted or not.
        """
        # Random and encrypt flag.
        flag_random:str = "0"
        if (is_random):
            flag_random ="1"
        flag_encrypt:str ="0"
        if (is_encrypt):
            flag_encrypt = "1"
            # TODO: Encrypt the message with RC4.
        # Start and End messages flag. 
        flag_start_message:str = stringToBinary("<?")
        flag_end_message:str = stringToBinary("?>")

        # File extension flag.
        flag_file_extension:str = stringToBinary(self.msg_extension)

        # Save modified message and return it.
        modified_message = arrayByteToBinary(self.message)
        modified_message = flag_random + flag_encrypt + flag_file_extension + flag_start_message + modified_message + flag_end_message
        self.modified_message = modified_message
        return modified_message


    def embed(self,enc_key:str=None, key:str=None, is_random:bool=False, is_encrypt:bool=False, output_file_name:str="") -> str:
        """
        Function to hide user message on audio. 
        Return output file path.

        Parameter.
        ----------
        enc_key: str, default none
            Key for encrypting message in RC4.
        key: str, default none
            Key for generating random table.
        is_random : bool, default false
            Boolean indicating lsb randomized or not.
        is_encrypt : bool, default false
            Boolean indicating message encrypted or not.
        """

        # Input validation.
        if (key and not(is_random)):
            raise Exception("Key inserted but message embedding not randomized")
        
        # Normalize message first.
        self.normalizeMessage(key, is_random, is_encrypt)

        # Generate access table.
        access_table = list(range(1, self.payload)) 
        if is_random and key:
            access_table = generate_random_access_table(key,self.payload)

        # Make sure you not randomize flag randomize position.
        self.audio_bytes[0]= modifyBit(self.audio_bytes[0],0,int(self.modified_message[0]))

        # Hide the message in audio_bytes using ordering from access_table.
        for messageIndex, audioIndex in enumerate(access_table, 1):
            if (messageIndex >= len(self.modified_message)):
                break
            self.audio_bytes[audioIndex] = modifyBit(self.audio_bytes[audioIndex],0,int(self.modified_message[messageIndex]))
        
        # Write file output.
        output_file_path = output_file_name
        if output_file_path == "":
            old_filename = ntpath.basename(self.audio_path).split('.')
            output_file_path = str(Path(self.audio_path).parent) + '/' + old_filename[0] + '_embedded.' + old_filename[1]
        else:
            output_file_path = output_file_path + '.wav'
        with wave.open(output_file_path, 'wb') as wav_file:
            wav_file.setparams(self.audio.getparams())
            wav_file.writeframes(self.audio_bytes)
            wav_file.close()

        return output_file_path

    def extract(self,output_file_name:str, enc_key:str=None, key:str=None)->str:
        """
        Function to extract user message from stego audio.
        Return path to extracted message file.

        Parameter.
        ----------
        enc_key: str, default none
            Key for encrypting message in RC4.
        key: str, default none
            Key for generating random table.
        output_file_path : str
            File name for output message.
        """
        # Check if stego audio lsb is randomized.
        print(ByteToBinary(self.audio_bytes[0])[-1], ByteToBinary(self.audio_bytes[1])[-1])
        is_random = False
        if (ByteToBinary(self.audio_bytes[0])[-1]=="1"):
            is_random = True
        if ((is_random and not(key)) or (not(is_random) and key)):
            raise Exception("You must provide key for this stego-audio file")
        
        # Generate access table based on randomized or not.
        access_table = list(range(1, self.payload)) 
        if is_random:
            access_table = generate_random_access_table(key,self.payload)

        # Get all LSB from audio_bytes.
        bit_message = ""
        for messageIndex, audioIndex in enumerate(access_table, 1):
            bit_message += str(ByteToBinary(self.audio_bytes[audioIndex])[-1])
        # Check flag encrypted.
        is_encrypted = False
        if (bit_message[0]=="1"):
            is_encrypted = True
        bit_message = bit_message[0:]

        # Transform binary string to bytearray like list.
        bytes_message = binarytoArrayBynary(bit_message)

        # Search for file extension.
        file_extension = ""
        for index, object in enumerate (bytes_message):
            file_extension += chr(int(object,2))
            if (chr(int(bytes_message[index+1],2)) == "<" and chr(int(bytes_message[index+2],2)) == "?"):
                break
        
        # Search for real message content.
        start_message_index = index + 3
        message = ""

        for index, object in enumerate (bytes_message, start_message_index):
            message += chr(int(object,2))
            if (chr(int(bytes_message[index+1],2)) == "?" and chr(int(bytes_message[index+2],2)) == ">"):
                break

        message = bytes(message)

        # Check if ecnrypted but user doesn't provide key.
        if (is_encrypted and not(enc_key)):
            raise Exception("You must provide decription key for extractting this message. ")
        # TODO : Decrypt the text.
        # if (is_encrypted):
        #     message = decrypt(key, decoded_msg)

        # Write file output.
        output_file_path = output_file_name + '.' + file_extension    
        new_file = open(output_file_path, "wb")
        new_file.write(message)
        new_file.close()

        return output_file_path


if __name__=="__main__":
    
    # Embed message.
    a:AudioStegano = AudioStegano("./testing/file_example_WAV_1MG.wav","./testing/aku.txt")
    a.embed(output_file_name="./testing/Wakaranai")

    # Extract message.
    b:AudioStegano = AudioStegano("./testing/Wakaranai.wav")
    b.extract("./testing/aku2.txt")
