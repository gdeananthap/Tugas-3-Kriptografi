# Python module.
from io import FileIO
import os
from typing import List
import wave
import ntpath

from pathlib import Path

# Own module.
from helper import ByteToBinary, binarytoArrayBynary, generate_random_access_table, modifyBit, \
    stringToBinary, arrayByteToBinary

class AudioStegano:
    """
    A class used for representing Steganography with audio.

    Attributes.
    ----------
    audio : WavAudio
        Audio is basic wav audio readed by wave. Audio can be container object or stego object.
    audio_path : str
        Absolute path to audio file.
    audio_bytes : bytesarray
        Audio in list of byte representation.
    payload : int
        Number of maximum bit you can insert to audio.
    message : bytesarray
        Message in list of byte representation.
    msg_extension : str
        File extension of the message.
    modified_message : str
        Message in binary string representantion.
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
        self.audio_path:str = audio_path
        # Get audio bytes representation.
        audio_frames = self.audio.readframes(self.audio.getnframes())
        self.audio_bytes:bytearray = bytearray(list(audio_frames))
        self.payload:int = len(audio_frames)

        # Process input messages.
        if (input_message_path):
            # Check if file exist.
            messages:bytes = open(input_message_path, "rb").read()
            if (not(messages)):
                raise Exception("Input message not exist")
            self.message:bytes = messages
            self.msg_extension:str = os.path.splitext(input_message_path)[1].lower()[1:]
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
        modified_message:str = arrayByteToBinary(self.message)
        modified_message = flag_random + flag_encrypt + flag_file_extension + flag_start_message \
            + modified_message + flag_end_message
        self.modified_message:str = modified_message
        return modified_message


    def embed(self,enc_key:str=None, key:str=None, is_random:bool=False, is_encrypt:bool=False, 
        output_file_name:str="") -> str:
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
        access_table:List[int] = list(range(1, self.payload)) 
        if is_random and key:
            access_table = generate_random_access_table(key,self.payload)

        # Make sure you not randomize flag randomize position.
        self.audio_bytes[0]= modifyBit(self.audio_bytes[0],0,int(self.modified_message[0]))

        # Hide the message in audio_bytes using ordering from access_table.
        for messageIndex, audioIndex in enumerate(access_table, 1):
            if (messageIndex >= len(self.modified_message)):
                break
            self.audio_bytes[audioIndex] = modifyBit(self.audio_bytes[audioIndex], 0,
                int(self.modified_message[messageIndex]))
        
        # Write file output.
        output_file_path:str = output_file_name
        if output_file_path == "":
            old_filename:str = ntpath.basename(self.audio_path).split('.')
            output_file_path = str(Path(self.audio_path).parent) + '/' + old_filename[0] + \
                '_embedded.' + old_filename[1]
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
        is_random:bool = False
        if (ByteToBinary(self.audio_bytes[0])[-1]=="1"):
            is_random = True
        if ((is_random and not(key)) or (not(is_random) and key)):
            raise Exception("You must provide key for this stego-audio file")
        
        # Generate access table based on randomized or not.
        access_table:List[int] = list(range(1, self.payload)) 
        if is_random:
            access_table = generate_random_access_table(key,self.payload)

        # Get all LSB from audio_bytes.
        bit_message:str = ""
        for audioIndex in access_table :
            bit_message += (str(ByteToBinary(self.audio_bytes[audioIndex]))[-1])
        # Check flag encrypted.
        is_encrypted:bool = False
        if (bit_message[0]=="1"):
            is_encrypted = True
        bit_message = bit_message[1:]

        # Transform binary string to bytearray like list.
        bytes_message:List[int] = binarytoArrayBynary(bit_message)

        # Search for file extension.
        file_extension:str = ""
        for index, object in enumerate (bytes_message):
            file_extension += chr(int(object,2))
            if (chr(int(bytes_message[index+1],2)) == "<" and chr(int(bytes_message[index+2],2)) \
                == "?"):
                break
        
        # Search for real message content.
        start_message_index = index + 3
        message = []

        for i in range(start_message_index, self.payload):
            message.append(int(bytes_message[i],2))
            if (chr(int(bytes_message[i+1],2)) == "?" and chr(int(bytes_message[i+2],2)) == ">"):
                break
        message:bytes = bytes(message)

        # Check if ecnrypted but user doesn't provide key.
        if (is_encrypted and not(enc_key)):
            raise Exception("You must provide decription key for extractting this message. ")
        # TODO : Decrypt the text.
        # if (is_encrypted):
        #     message = decrypt(key, message)

        # Write file output.
        output_file_path:str = output_file_name + '.' + file_extension    
        new_file:FileIO = open(output_file_path, "wb")
        new_file.write(message)
        new_file.close()

        return output_file_path


def main():
    case = int(input("Masukkan pilihan: "))
    # Embed text to audio.
    if (case == 1):
        # Embed message.
        a:AudioStegano = AudioStegano("./testing/sample_1.wav","./testing/message.txt")
        a.embed(output_file_name="./testing/stego_text_in_audio")

        # Extract message.
        b:AudioStegano = AudioStegano("./testing/stego_text_in_audio.wav")
        b.extract(output_file_name="./testing/extract_message")
    
    # Embed audio to audio.
    elif (case == 2):
        # Embed message.
        a:AudioStegano = AudioStegano("./testing/sample_1.wav","./testing/message.wav")
        a.embed(output_file_name="./testing/stego_audio_in_audio")

        # Extract message.
        b:AudioStegano = AudioStegano("./testing/stego_audio_in_audio.wav")
        b.extract(output_file_name="./testing/extract_message")
    
    # Embed picture to audio.
    elif (case == 3):
        # Embed message.
        a:AudioStegano = AudioStegano("./testing/sample_2.wav","./testing/message.png")
        a.embed(output_file_name="./testing/stego_image_in_audio")

        # Extract message.
        b:AudioStegano = AudioStegano("./testing/stego_image_in_audio.wav")
        b.extract(output_file_name="./testing/extract_message")
    
    # Embed video to audio.
    elif (case == 4):
        # Embed message.
        a:AudioStegano = AudioStegano("./testing/sample_3.wav","./testing/message.avi")
        a.embed(output_file_name="./testing/stego_video_in_audio")

        # Extract message.
        b:AudioStegano = AudioStegano("./testing/stego_video_in_audio.wav")
        b.extract(output_file_name="./testing/extract_message")

    # Embed text to audio with randomized lsb.
    elif (case == 5):
        # Embed message.
        a:AudioStegano = AudioStegano("./testing/sample_1.wav","./testing/message.txt")
        a.embed(output_file_name="./testing/stego_text_in_audio", is_random=True, key="akuhaha")

        # Extract message.
        b:AudioStegano = AudioStegano("./testing/stego_text_in_audio.wav")
        b.extract(output_file_name="./testing/extract_message", key="akuhaha")
    
    # Embed audio to audio with randomized lsb.
    elif (case == 6):
        # Embed message.
        a:AudioStegano = AudioStegano("./testing/sample_1.wav","./testing/message.wav")
        a.embed(output_file_name="./testing/stego_audio_in_audio", is_random=True, key="akuma")

        # Extract message.
        b:AudioStegano = AudioStegano("./testing/stego_audio_in_audio.wav")
        b.extract(output_file_name="./testing/extract_message", key="akuma")
    
    # Embed picture to audio with randomized lsb.
    elif (case == 7):
        # Embed message.
        a:AudioStegano = AudioStegano("./testing/sample_2.wav","./testing/message.png")
        a.embed(output_file_name="./testing/stego_image_in_audio", is_random=True, key="oni-chan")

        # Extract message.
        b:AudioStegano = AudioStegano("./testing/stego_image_in_audio.wav")
        b.extract(output_file_name="./testing/extract_message", key="oni-chan")
    
    # Embed video to audio with randomized lsb.
    elif (case == 8):
        # Embed message.
        a:AudioStegano = AudioStegano("./testing/sample_3.wav","./testing/message.avi")
        a.embed(output_file_name="./testing/stego_video_in_audio", is_random=True, key="oppai")

        # Extract message.
        b:AudioStegano = AudioStegano("./testing/stego_video_in_audio.wav")
        b.extract(output_file_name="./testing/extract_message", key="oppai")
    
if __name__=="__main__":
    main()
