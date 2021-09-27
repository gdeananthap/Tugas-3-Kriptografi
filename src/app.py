import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, current_app
from flask.helpers import send_file
from werkzeug.datastructures import FileStorage
import traceback

from audioStegano import AudioStegano
from rc4 import encrypt, encryptByte, decrypt, decryptByte
from imageStegano import ImageStegano

# Flask Configuration.
app = Flask(__name__)
UPLOAD_FOLDER = './static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'mysecret'

"""
--------------------------------------------------------------
# Default Route
--------------------------------------------------------------
"""
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
	return redirect(url_for('rc4'))

"""
--------------------------------------------------------------
# Download File Route
--------------------------------------------------------------
"""
@app.route('/download/<filename>')
def download(filename):
  return send_from_directory(os.path.join(current_app.root_path, app.config['UPLOAD_FOLDER']), filename, as_attachment=True)

"""
--------------------------------------------------------------
# Route for RC4 Cipher
--------------------------------------------------------------
"""
# Index route.
@app.route('/rc4-cipher')
def rc4():
  return render_template('pages/rc4-cipher.html', encrypt=True)

# Encrypt route.
@app.route('/rc4-cipher/encrypt',  methods=['POST', 'GET'])
def rc4Encrypt():
	if request.method == 'POST':
		if(request.form["encrypt"]=="encrypt-file"):
			plaintext = request.form['plaintext']
			key = request.form['key']
			ciphertext = encrypt(plaintext, key)
			return render_template('pages/rc4-cipher.html', encrypt=True, plaintext=plaintext, key=key, result_ciphertext=ciphertext)
		else:
			key = request.form['key']
			file = request.files['file-plaintext']
			file_contents = file.read()
			filename = file.filename
			cipher_file = encryptByte(file_contents, key)
			return send_file(cipher_file, as_attachment=True, attachment_filename="encrypted-"+filename)
	else:
		return redirect(url_for('rc4'))

# Decrypt route.
@app.route('/rc4-cipher/decrypt',  methods=['POST', 'GET'])
def rc4Decrypt():
	if request.method == 'POST':
		if(request.form["decrypt"]=="encrypt-file"):
			ciphertext = request.form['ciphertext']
			key = request.form['key']
			plaintext = decrypt(ciphertext, key)
			return render_template('pages/rc4-cipher.html', encrypt=False, result_plaintext=plaintext, key=key, ciphertext=ciphertext)
		else:
			key = request.form['key']
			file = request.files['file-ciphertext']
			file_contents = file.read()
			filename = file.filename
			decipher_file = decryptByte(file_contents, key)
			return send_file(decipher_file, as_attachment=True, attachment_filename="decrypted-"+filename)
	else:
		return redirect(url_for('rc4'))

"""
--------------------------------------------------------------
# Route for Image Steganography
--------------------------------------------------------------
"""
# Index route.
@app.route('/image-steganography')
def imageStegano():
	return render_template('pages/image-steganography.html', embed=True)

# Embed route.
@app.route('/image-steganography/embed', methods=['POST', 'GET'])
def imageSteganoEmbed():
	if request.method == 'POST':
		# Get request payload.
		is_random = request.form['embed-method'] == "random" or False
		is_encrypt = request.form['message-rc4'] == "encrypt" or False 
		key_random = request.form['key-random']  or None
		key_encrypt = request.form['key-encrypt'] or None
		print(key_random, key_encrypt, is_random, is_encrypt)
		output_filename = request.form['output-name']
		output_filename = os.path.join(current_app.root_path, app.config['UPLOAD_FOLDER'], output_filename)
		
		# Catch exception when embedding message.
		try:
			# Save the uploaded file to local.
			# Save image file.
			file_image = request.files['file-image']
			file_image.stream.seek(0)
			file_image_path = os.path.join(current_app.root_path, app.config['UPLOAD_FOLDER'], file_image.filename)
			file_image.save(file_image_path)
			# Save message file.
			file_message = request.files['file-message']
			file_message.stream.seek(0)
			file_message_path = os.path.join(current_app.root_path, app.config['UPLOAD_FOLDER'], file_message.filename)
			file_message.save(file_message_path)
	
			# Embed the message.
			image_stegano:ImageStegano = ImageStegano(file_image_path, file_message_path)
			output_filepath = image_stegano.embed(enc_key=key_encrypt, key=key_random, is_random=is_random, 
				is_encrypt=is_encrypt, output_file_name=output_filename)
			# Calculate psnr 
			PSNR = ImageStegano.calculatePSNR(file_image_path,output_filepath)
			return render_template('pages/image-steganography.html', embed=True, psnr=PSNR, output_filename = os.path.basename(output_filepath))
		
		except (Exception) as e:
			# Render error webpage.
			return render_template('pages/image-steganography.html', embed=True, error = e, form = request.form)
	else:
		if request.method == 'POST':
			pass
		else:
			return redirect(url_for('imageStegano'))

# Extract route.
@app.route('/image-steganography/extract', methods=['POST', 'GET'])
def imageSteganoExtract():
	if request.method == 'POST':
		# Get request payload.
		key_random = request.form['key-random']  or None
		key_encrypt = request.form['key-encrypt'] or None
		output_filename = request.form['output-name']
		output_filename = os.path.join(current_app.root_path, app.config['UPLOAD_FOLDER'], output_filename)
		
		# Catch exception when embedding message.
		try:
			# Save the uploaded file to local.
			# Save image file.
			file_stego_image = request.files['file-stego-image']
			file_stego_image.stream.seek(0)
			file_stego_image_path = os.path.join(current_app.root_path, app.config['UPLOAD_FOLDER'], file_stego_image.filename)
			file_stego_image.save(file_stego_image_path)
		
			# Extract the message.
			image_stegano:ImageStegano = ImageStegano(file_stego_image_path)
			output_filepath = image_stegano.extract(output_filename, enc_key=key_encrypt, key=key_random)
			extension = os.path.splitext(output_filepath)[1].lower()

			return send_from_directory(os.path.join(current_app.root_path, app.config['UPLOAD_FOLDER']), request.form['output-name'] + extension, as_attachment=True)
		except (Exception) as e:
			# Render error webpage.
			return render_template('pages/image-steganography.html', embed=False,
			error = e, form = request.form)
	else:
		# Render default webpage. 
		return redirect(url_for('imageStegano'))


"""
--------------------------------------------------------------
# Route for Audio Steganography
--------------------------------------------------------------
"""
# Index route.
@app.route('/audio-steganography')
def audioStegano():
	return render_template('pages/audio-steganography.html', embed=True)

# Embed route.
@app.route('/audio-steganography/embed', methods=['POST', 'GET'])
def audioSteganoEmbed():
	if request.method == 'POST':
		# Get request payload.
		is_random = request.form['embed-method'] == "random" or False
		is_encrypt = request.form['message-rc4'] == "encrypt" or False 
		key_random = request.form['key-random']  or None
		key_encrypt = request.form['key-encrypt'] or None
		output_filename = request.form['output-name']
		output_filename = os.path.join(current_app.root_path, app.config['UPLOAD_FOLDER'], output_filename)
		
		# Catch exception when embedding message.
		try:
			# Save the uploaded file to local.
			# Save audio file.
			file_audio = request.files['file-audio']
			file_audio.stream.seek(0)
			file_audio_path = os.path.join(current_app.root_path, app.config['UPLOAD_FOLDER'], file_audio.filename)
			file_audio.save(file_audio_path)
			# Save message file.
			file_message = request.files['file-message']
			file_message.stream.seek(0)
			file_message_path = os.path.join(current_app.root_path, app.config['UPLOAD_FOLDER'], file_message.filename)
			file_message.save(file_message_path)
	
			# Embed the message.
			audio_stegano:AudioStegano = AudioStegano(file_audio_path, file_message_path)
			output_filepath = audio_stegano.embed(enc_key=key_encrypt, key=key_random, is_random=is_random, 
				is_encrypt=is_encrypt, output_file_name=output_filename)
			# Calculate psnr 
			PSNR = AudioStegano.calculatePSNR(file_audio_path,output_filepath)
			return render_template('pages/audio-steganography.html', embed=True, psnr=PSNR, output_filename = request.form['output-name']+".wav")
		
		except (Exception) as e:
			# Render error webpage.
			return render_template('pages/audio-steganography.html', embed=True,
			error = e, form = request.form)
	else:
		# Render default webpage. 
		return redirect(url_for('audioStegano'))

# Extract route.
@app.route('/audio-steganography/extract', methods=['POST', 'GET'])
def audioSteganoExtract():
	if request.method == 'POST':
		# Get request payload.
		key_random = request.form['key-random']  or None
		key_encrypt = request.form['key-encrypt'] or None
		output_filename = request.form['output-name']
		output_filename = os.path.join(current_app.root_path, app.config['UPLOAD_FOLDER'], output_filename)
		
		# Catch exception when embedding message.
		try:
			# Save the uploaded file to local.
			# Save audio file.
			file_stego_audio = request.files['file-stego-audio']
			file_stego_audio.stream.seek(0)
			file_stego_audio_path = os.path.join(current_app.root_path, app.config['UPLOAD_FOLDER'], file_stego_audio.filename)
			file_stego_audio.save(file_stego_audio_path)
		
			# Extrac the message.
			audio_stegano:AudioStegano = AudioStegano(file_stego_audio_path)
			output_filepath = audio_stegano.extract(output_filename, enc_key=key_encrypt, key= key_random)
			extension = os.path.splitext(output_filepath)[1].lower()
			print(request.form['output-name'] + "." + extension)
			return send_from_directory(os.path.join(current_app.root_path, app.config['UPLOAD_FOLDER']), request.form['output-name'] + extension, as_attachment=True)

		
		except (Exception) as e:
			# Render error webpage.
			return render_template('pages/audio-steganography.html', encrypt=False,
			error = e, form = request.form)
	else:
		# Render default webpage. 
		return redirect(url_for('audioStegano'))


"""
--------------------------------------------------------------
# Flask Main Program
--------------------------------------------------------------
"""
if __name__ == '__main__':
	app.run(debug=True,threaded=True)