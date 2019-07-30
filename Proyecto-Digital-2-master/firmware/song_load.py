import wave

class SongLoad():
    def __init__(self, name_song):
        self.file_name = name_song
        self.file = wave.open(self.file_name,'rb')
        self.totalMuestras = self.file.getnframes()

    def byteArray(self):
        Count_muestra = 0
        muestras = []
        while Count_muestra < self.totalMuestras:
            frame = self.file.readframes(1)
            # Assumes 16 bit frame
            lsb = frame[0] #right bit
            msb = frame[1] #left bit
            muestra = (msb << 8) + lsb
            #print('{0:08b} {1:08b} -> {2:016b}'.format(b2, b1, b))
            muestras.append(muestra)
            Count_muestra += 1
        return muestras

    def twosToOnes(self, bArray):
        onesArray = []
        for b in bArray:
            if b > 0x8000:
                b2 = 0x8000 - (0xffff & (~b + 1))
            else:
                b2 = b + 0x8000
            onesArray.append(b2)
        return(onesArray)

    def byteFormatedString(self, bArray):
        bStrings = []
        for idx, val in enumerate(bArray):
            hexStr = ''
            if ((idx % 30 == 0) and (idx > 0)):
                hexStr += '\n'
            hexStr += ('0x{:04x}'.format(val))
            bStrings.append(hexStr)
        return  ",".join(bStrings)


    def writeFile(self):
        txtName = self.file_name.replace('.wav', '.h')
        txt = open(txtName, 'w')
        txt.truncate()
        txt.write('\n\n// Auto generated\nint frame_count = {};\n'.format(self.totalMuestras))
        txt.write('const uint16_t wave_data[{}] =\n'.format(self.totalMuestras))
        txt.write('{')
        bArray = self.byteArray()
        bArray = self.twosToOnes(bArray)
        print(bArray)
        txt.write(self.byteFormatedString(bArray))
        txt.write('};\n')
        txt.close()

def main():
    fpath = 'get_lucky_daft_punk.wav'
    wav = SongLoad(fpath)
    print('writing file')
    wav.writeFile()
    print(wav.file.getparams())
    wav.file.close()
    print('done')


main()
