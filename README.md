# Modified RC4 and Steganografi with LSB
## Semester I Tahun 2021/2022

### Tugas Besar I IF4020 Kriptografi

*Program Studi Teknik Informatika* <br />
*Sekolah Teknik Elektro dan Informatika* <br />
*Institut Teknologi Bandung* <br />

*Semester I Tahun 2021/2022*

## Description
Program stream cipher yang memodifikasi RC4 (modified RC4) dalam Bahasa Python berbasis Web dengan framework flask. Prosedur KSA dan PRGA di dalam RC4, telah dimodifikasi sedemikian hingga algoritma menjadi semakin kompleks dan susah dipecahkan. Program juga dapat melakukan steganografi pada citra digital dan pada audio dengan metode LSB. Format citra yang digunakan adalah BMP (bitmap) dan PNG (Portable Network Graphics). Format BMP tidak terkompresi, sedangkan format PNG terkompresi dengan metode kompresi lossless. Format audio yang digunakan adalah WAV. Format ini tidak terkompresi.
   
## Author
1. Gde Anantha Priharsena (13519026)
2. Reihan Andhika Putra (13519043)
3. Reyhan Emyr Arrosyid (13519167)

## Requirements
- [Python 3](https://www.python.org/downloads/)

## Installation And Run
Clone the repository
```bash
git clone https://github.com/hokkyss/Stima03_OTOBOT.git
cd src
```
### Automatic Setup
#### First Time Setup
1. Open `setup.bat`
2. Wait until the installation is finished
3. The setup will automatically open the web browser
4. If the page failed to load, wait a moment then refresh the page

#### Run
1. Open `run.bat`
2. It will automatically open the web browser
3. If the page failed to load, wait a moment then refresh the page

#### Manual Setup
After cloning the repository
```bash 
cd src
python -m venv virt
virt\Scripts\activate
pip install -r requirements.txt
python app.py
```
Then open your web browser and go to [localhost:5000](http://localhost:5000)

## Screen Capture 
### Modified RC4
### Image Steganography
### Audio Steganography
