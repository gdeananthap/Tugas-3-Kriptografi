import io

def swap(s, i, j):
    temp = s[i]
    s[i] = s[j]
    s[j] = temp
    return s

def ksa(key):
    s = [0 for i in range(256)]
    for i in range(256):
        s[i] = i
    j = 0
    for i in range(256):
        j = (j+s[i]+ord(key[i%len(key)]))%256
        s = swap(s, i, j)
    return s

def prga(text, s, mode="encrypt"):
    i = 0
    j = 0
    if(mode=="encrypt"):
        c = ""
        for idx in range(len(text)):
            i = (i+1) % 256
            j = (j+s[i]) % 256
            s = swap(s, i, j)
            t = (s[i]+s[j]) % 256
            u = s[t]
            c += hex(u^ord(text[idx])^j)[2:].zfill(2).upper()
        return c
    elif(mode=="encrypt-byte"):
        c = bytearray()
        for idx in range(len(text)):
            i = (i+1) % 256
            print(type(j))
            print(type(s[i]))
            j = (j+s[i]) % 256
            s = swap(s, i, j)
            t = (s[i]+s[j]) % 256
            u = s[t]
            c.append(u^text[idx]^j)
        return c
    elif(mode=="decrypt"):
        text = [text[k:k+2]for k in range(0,len(text),2)]
        p = ""
        for idx in range(len(text)):
            i = (i+1) % 256
            j = (j+s[i]) % 256
            s = swap(s, i, j)
            t = (s[i]+s[j]) % 256
            u = s[t]
            p += hex(u^int(text[idx], 16)^j)[2:].zfill(2).upper()
        p = ''.join(chr(int(p[l:l+2], 16)) for l in range(0, len(p), 2))
        return p
    else: #(mode=="encrypt-byte")
        p = bytearray()
        for idx in range(len(text)):
            i = (i+1) % 256
            j = (j+s[i]) % 256
            s = swap(s, i, j)
            t = (s[i]+s[j]) % 256
            u = s[t]
            p.append(u^text[idx]^j)
        return p

def encrypt(text, key):
    s = ksa(key)
    c = prga(text, s)
    return c

def encryptByte(text, key):
    s = ksa(key)
    c = prga(text, s, "encrypt-byte")
    return io.BytesIO(c)

def decrypt(text, key):
    s = ksa(key)
    p = prga(text, s, "decrypt")
    return p

def decryptByte(text, key):
    s = ksa(key)
    p = prga(text, s, "encrypt-byte")
    return io.BytesIO(p)

# Main Program
def main():
    key = input("Enter key: ")
    p = input("Enter plaintext: ")
    # encrypt
    enkripsi = encrypt(p, key);
    print(enkripsi)
    # decrypt
    dekripsi = decrypt(enkripsi, key)
    print(dekripsi)

# If module is being runned.
if __name__ == "__main__":
    main()

