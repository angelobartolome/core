import base64

from Crypto.Cipher import AES

from .cryptocrc import CryptoCRC


class ACUnitEncryptionService:
    def __init__(self, key):
        self.key = base64.b64decode(key)

    def aes_cfb_decrypt(self, iv, ciphertext):
        cipher = AES.new(self.key, AES.MODE_CFB, iv=iv, segment_size=128)
        plaintext = cipher.decrypt(ciphertext)
        return plaintext

    def aes_cfb_encrypt(self, iv, plaintext):
        cipher = AES.new(self.key, AES.MODE_CFB, iv=iv, segment_size=128)
        ciphertext = cipher.encrypt(plaintext)
        return ciphertext

    def encrypt(self, plaintext):
        bytedata = bytes(plaintext + "BZ", "utf-8")
        # Generate IV
        iv = AES.new(self.key, AES.MODE_CFB).iv

        # Encrypt data
        ciphertext = self.aes_cfb_encrypt(iv, bytedata)

        # Prepare data for CRC
        length = len(ciphertext)
        bArr2 = bytearray(length + 18)
        i2 = 0
        i3 = 0
        while i2 < 16:
            bArr2[i2] = iv[i2]
            i2 += 1
            i3 += 1

        i4 = 0
        while i4 < length:
            bArr2[i3] = ciphertext[i4]
            i4 += 1
            i3 += 1

        calcCRC = CryptoCRC.caluCRC(0, bArr2, length + 16)
        bArr2[i3] = calcCRC & 255
        bArr2[i3 + 1] = (calcCRC >> 8) & 255

        encoded_ciphertext = base64.b64encode(bArr2).decode("utf-8")
        return encoded_ciphertext

    def decrypt(self, encoded_ciphertext):
        decode = base64.b64decode(encoded_ciphertext)
        iv = decode[:16]
        ciphertext = decode[17 : len(decode) - 1]

        plaintext = self.aes_cfb_decrypt(iv, ciphertext)
        return plaintext.decode("utf-8", "ignore")
