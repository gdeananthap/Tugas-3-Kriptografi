# Python module.
import os
import math
from typing import List
import ntpath
import numpy as np

from PIL import Image
from io import FileIO
from pathlib import Path

# Own module.
from helper import ByteToBinary, binarytoArrayBynary, generate_random_access_table, modifyBit, \
    stringToBinary, arrayByteToBinary

class ImageStegano:
    """
    A class used for representing Steganography with image.

    Attributes.
    ----------
    image : Image
        image is basic image file readed by Pillow library. Image can be container object or stego object.
    image_path : str
        Absolute path to image file.
    image_bytes : bytesarray
        Image in list of byte representation.
    image_extension: str
        Extension of the cover image
    max_payload_size : int
        Number of maximum bit you can insert to image.
    message : bytesarray
        Message in list of byte representation.
    msg_extension : str
        File extension of the message.
    modified_message : str
        Message in binary string representantion.
    """

    def __init__(self, image_path:str, input_message_path:str=None) -> None:
        """
        Constructor for ImageStegano class. Read input image file and input message file.
        Format for image must be BMP or PNG, input message can be any file.

        Parameter.
        ----------
        image_path : str
            Absolute path to image file.
        input_message_path : str
            Absolute path to message file.
        """

        # Check image file validity for processing.
        # Check extension.
        file_extension = os.path.splitext(image_path)[1].lower()
        if (file_extension != ".bmp" and file_extension != ".png"):
            raise Exception("Can only process bmp or png file for image")
        # Check if file exist.
        image = Image.open(image_path, "r")
        if (not(image)):
            raise Exception("Input image not exist")
       

        # Process image input.
        self.image = image
        self.image_path:str = image_path
        self.image_extension = file_extension

        # Get image bytes representation.
        self.image_bytes = bytearray(self.image.tobytes())
        self.max_payload_size:int = len(self.image_bytes)

        # Process input messages.
        if (input_message_path):
            # Check if file exist.
            messages:bytes = open(input_message_path, "rb").read()
            if (not(messages)):
                raise Exception("Input message not exist")
            self.message:bytes = messages
            self.msg_extension:str = os.path.splitext(input_message_path)[1].lower()[1:]
            # Check if current image file is big enough to hide message.
            # For each bytes(8 bit) you can only hide one bit from message. You also need to keep space 
            # for input file extension and randomized, encrypt, start and endfile flag. 
            if len(self.message) > self.max_payload_size//8 - len(self.msg_extension) - 5:
                raise Exception("Input message is too big")
        
        image.close()

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
        Function to hide user message on image. 
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
        elif (is_random and not key):
            raise Exception("You must provide a key for randomized method")
        elif (is_encrypt and not enc_key):
            raise Exception("You must provide a key for encryption")
        
        # Normalize message first.
        self.normalizeMessage(key, is_random, is_encrypt)

        # Generate access table.
        access_table:List[int] = list(range(1, self.max_payload_size)) 
        if is_random and key:
            access_table = generate_random_access_table(key,self.max_payload_size)

        # Make sure you not randomize flag randomize position.
        self.image_bytes[0]= modifyBit(self.image_bytes[0],0,int(self.modified_message[0]))

        # Hide the message in image_bytes using ordering from access_table.
        for messageIndex, imageIndex in enumerate(access_table, 1):
            if (messageIndex >= len(self.modified_message)):
                break
            self.image_bytes[imageIndex] = modifyBit(self.image_bytes[imageIndex], 0,
                int(self.modified_message[messageIndex]))
        
        # Write file output.
        output_file_path:str = output_file_name
        if ntpath.basename(output_file_path).split('.')[0] == "":
            old_filename:str = ntpath.basename(self.image_path).split('.')
            output_file_path = str(Path(self.image_path).parent) + '/' + old_filename[0] + \
                '_embedded.' + old_filename[1]
        else:
            output_file_path = output_file_path + self.image_extension

        with Image.frombytes(self.image.mode, self.image.size, bytes(self.image_bytes)) as new_image:
            new_image.save(output_file_path, self.image.format)
            new_image.close()

        return output_file_path

    def extract(self,output_file_name:str, enc_key:str=None, key:str=None)->str:
        """
        Function to extract user message from stego image.
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
        # Check if stego image lsb is randomized.
        is_random:bool = False
        if (ByteToBinary(self.image_bytes[0])[-1]=="1"):
            is_random = True
        if ((is_random and not(key)) or (not(is_random) and key)):
            raise Exception("You must provide key for this stego-image file")
        
        # Generate access table based on randomized or not.
        access_table:List[int] = list(range(1, self.max_payload_size)) 
        if is_random:
            access_table = generate_random_access_table(key,self.max_payload_size)

        # Get all LSB from image_bytes.
        bit_message:str = ""
        for imageIndex in access_table :
            bit_message += (str(ByteToBinary(self.image_bytes[imageIndex]))[-1])
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

        for i in range(start_message_index, self.max_payload_size):
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
    
    @staticmethod
    def calculatePSNR(image_path:str, stego_image_path:str) -> float:
        """
        Function to calculate psnr of two image file. The original and the embedded image.
        Return float representing the psnr.

        Parameter.
        ----------
        image_path : str
            Absolute path to image file.
        stego_image_path : str
            Absolute path to stego image file.
        """
        # Validate if file exist.
        try:
            image = Image.open(image_path, "r")
            stego_image = Image.open(stego_image_path, 'r')    
        except:
            raise Exception("File not exist")
        
        # Read both file frame and store the data in bytearray.
        # Read image data.
        image_bytes = bytearray(image.tobytes())
        image_bytes_length = len(image_bytes)
        image.close()
        # Read stego image data.
        stego_image_bytes = bytearray(stego_image.tobytes())
        stego_image.close()

        # Calculate the rms.
        image_bytes_2 = np.array(image_bytes)
        stego_image_bytes_2 = np.array(stego_image_bytes)
        difference_array = np.subtract(image_bytes_2, stego_image_bytes_2)
        squared_array = np.square(difference_array)
        sum_squared_array = np.sum(squared_array)
        rms = sum_squared_array / image_bytes_length
        
        # Calculate the psnr. 
        psnr = 20 * math.log10(255 / math.sqrt(rms))
        return psnr       


def main():
    case = int(input("Masukkan pilihan: "))
    # Embed text to image.
    if (case == 1):
        # Embed message.
        a:ImageStegano = ImageStegano("./testing/png_image_sample.png","./testing/message.txt")
        a.embed(output_file_name="./testing/stego_text_in_image")

        # Extract message.
        b:ImageStegano = ImageStegano("./testing/stego_text_in_image.png")
        b.extract(output_file_name="./testing/extract_message")

        # PSNR
        print("PSNR:", ImageStegano.calculatePSNR("./testing/png_image_sample.png","./testing/stego_text_in_image.png"))
    
    # Embed audio to image.
    elif (case == 2):
        # Embed message.
        a:ImageStegano = ImageStegano("./testing/png_image_sample.png","./testing/message.wav")
        a.embed(output_file_name="./testing/stego_audio_in_image")

        # Extract message.
        b:ImageStegano = ImageStegano("./testing/stego_audio_in_image.png")
        b.extract(output_file_name="./testing/extract_message")

        # PSNR
        print("PSNR:", ImageStegano.calculatePSNR("./testing/png_image_sample.png","./testing/stego_audio_in_image.png"))
    
    # Embed image to image.
    elif (case == 3):
        # Embed message.
        a:ImageStegano = ImageStegano("./testing/bmp_image_sample_1.bmp","./testing/message.png")
        a.embed(output_file_name="./testing/stego_image_in_image")

        # Extract message.
        b:ImageStegano = ImageStegano("./testing/stego_image_in_image.bmp")
        b.extract(output_file_name="./testing/extract_message")

        # PSNR
        print("PSNR:", ImageStegano.calculatePSNR("./testing/bmp_image_sample_1.bmp","./testing/stego_image_in_image.bmp"))
    
    # Embed video to image.
    elif (case == 4):
        # Embed message.
        a:ImageStegano = ImageStegano("./testing/bmp_image_sample_2.bmp","./testing/message.avi")
        a.embed(output_file_name="./testing/stego_video_in_image")

        # Extract message.
        b:ImageStegano = ImageStegano("./testing/stego_video_in_image.bmp")
        b.extract(output_file_name="./testing/extract_message")

        # PSNR
        print("PSNR:", ImageStegano.calculatePSNR("./testing/bmp_image_sample_2.bmp","./testing/stego_video_in_image.bmp"))

    # Embed text to image with randomized lsb.
    elif (case == 5):
        # Embed message.
        a:ImageStegano = ImageStegano("./testing/png_image_sample.png","./testing/message.txt")
        a.embed(output_file_name="./testing/stego_text_in_image", is_random=True, key="kripto")

        # Extract message.
        b:ImageStegano = ImageStegano("./testing/stego_text_in_image.png")
        b.extract(output_file_name="./testing/extract_message", key="kripto")

        # PSNR
        print("PSNR:", ImageStegano.calculatePSNR("./testing/png_image_sample.png","./testing/stego_text_in_image.png"))
    
    # Embed audio to image with randomized lsb.
    elif (case == 6):
        # Embed message.
        a:ImageStegano = ImageStegano("./testing/png_image_sample.png","./testing/message.wav")
        a.embed(output_file_name="./testing/stego_audio_in_image", is_random=True, key="badutsirkus")

        # Extract message.
        b:ImageStegano = ImageStegano("./testing/stego_audio_in_image.png")
        b.extract(output_file_name="./testing/extract_message", key="badutsirkus")

        # PSNR
        print("PSNR:", ImageStegano.calculatePSNR("./testing/png_image_sample.png","./testing/stego_audio_in_image.png"))
    
    # Embed image to image with randomized lsb.
    elif (case == 7):
        # Embed message.
        a:ImageStegano = ImageStegano("./testing/bmp_image_sample_1.bmp","./testing/message.png")
        a.embed(output_file_name="./testing/stego_image_in_image", is_random=True, key="kuncistego")

        # Extract message.
        b:ImageStegano = ImageStegano("./testing/stego_image_in_image.bmp")
        b.extract(output_file_name="./testing/extract_message", key="kuncistego")

         # PSNR
        print("PSNR:", ImageStegano.calculatePSNR("./testing/bmp_image_sample_1.bmp","./testing/stego_image_in_image.bmp"))
    
    # Embed video to image with randomized lsb.
    elif (case == 8):
        # Embed message.
        a:ImageStegano = ImageStegano("./testing/bmp_image_sample_2.bmp","./testing/message.avi")
        a.embed(output_file_name="./testing/stego_video_in_image", is_random=True, key="random")

        # Extract message.
        b:ImageStegano = ImageStegano("./testing/stego_video_in_image.bmp")
        b.extract(output_file_name="./testing/extract_message", key="random")

         # PSNR
        print("PSNR:", ImageStegano.calculatePSNR("./testing/bmp_image_sample_2.bmp","./testing/stego_video_in_image.bmp"))
    
if __name__=="__main__":
    main()
