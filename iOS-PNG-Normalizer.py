'''
iOS-PNG-Normalizer v2.0
By CNDY
https://github.com/CNDY1390/iOS-PNG-Normalizer

This program is free software.

License
GNU3.0
General Public License v3.0
'''

from struct import unpack, pack
from zlib import decompress, compress, crc32
import stat
import sys
import os


def getNormalizedPNG(filename):
    pngheader = b"\x89PNG\r\n\x1a\n"

    with open(filename, "rb") as file:
        oldPNG = file.read()

    if oldPNG[:8] != pngheader:
        return None

    newPNG = oldPNG[:8]

    chunkPos = len(newPNG)

    idatAcc = b""
    breakLoop = False

    # For each chunk in the PNG file
    while chunkPos < len(oldPNG):

        skip = False

        # Reading chunk
        chunkLength = oldPNG[chunkPos:chunkPos+4]
        chunkLength = unpack(">L", chunkLength)[0]
        chunkType = oldPNG[chunkPos+4:chunkPos+8]
        chunkData = oldPNG[chunkPos+8:chunkPos+8+chunkLength]
        chunkCRC = oldPNG[chunkPos+chunkLength+8:chunkPos+chunkLength+12]
        chunkCRC = unpack(">L", chunkCRC)[0]
        chunkPos += chunkLength + 12

        # Parsing the header chunk
        if chunkType == b"IHDR":
            width = unpack(">L", chunkData[0:4])[0]
            height = unpack(">L", chunkData[4:8])[0]

        # Parsing the image chunk
        if chunkType == b"IDAT":
            # Store the chunk data for later decompression
            idatAcc += chunkData
            skip = True

        # Removing CgBI chunk
        if chunkType == b"CgBI":
            skip = True

        # Add all accumulated IDATA chunks
        if chunkType == b"IEND":

            try:
                # Uncompressing the image chunk
                bufSize = width * height * 4 + height
                chunkData = decompress(idatAcc, -15, bufSize)

            except Exception as e:
                # The PNG image is normalized
                print(e)
                return None

            chunkType = b"IDAT"

            # Swapping red & blue bytes for each pixel
            newdata = []
            for y in range(height):
                i = len(newdata)
                newdata.append(chunkData[i:i+1])
                for x in range(width):
                    i = len(newdata)
                    newdata.append(chunkData[i+2:i+3])
                    newdata.append(chunkData[i+1:i+2])
                    newdata.append(chunkData[i:i+1])
                    newdata.append(chunkData[i+3:i+4])

            # Compressing the image chunk
            chunkData = b''.join(newdata)
            chunkData = compress(chunkData)
            chunkLength = len(chunkData)
            chunkCRC = crc32(chunkType)
            chunkCRC = crc32(chunkData, chunkCRC)
            chunkCRC = (chunkCRC + 0x100000000) % 0x100000000
            breakLoop = True

        if not skip:
            newPNG += pack(">L", chunkLength)
            newPNG += chunkType
            if chunkLength > 0:
                newPNG += chunkData
            newPNG += pack(">L", chunkCRC)
        if breakLoop:
            break

    return newPNG


def updatePNG(filename):
    data = getNormalizedPNG(filename)
    if data is not None:
        with open(filename, "wb") as file:
            file.write(data)
        return True
    return data


def getFiles(base):
    global _dirs
    global _pngs
    if base == ".":
        _dirs = []
        _pngs = []

    if base in _dirs:
        return

    files = os.listdir(base)
    for file in files:
        filepath = os.path.join(base, file)
        try:
            st = os.lstat(filepath)
        except os.error:
            continue

        if stat.S_ISDIR(st.st_mode):
            if filepath not in _dirs:
                getFiles(filepath)
                _dirs.append(filepath)

        elif file[-4:].lower() == ".png":
            if filepath not in _pngs:
                _pngs.append(filepath)

    if base == ".":
        return _dirs, _pngs


print("-------------------------")
print(" iOS PNG Normalizer v2.0 ")
print("-------------------------")
print(" ")
print("[+] Searching PNG files...", end=' ')
dirs, pngs = getFiles(".")
print("ok")

if len(pngs) == 0:
    print(" ")
    print("[!] Alert: There are no PNG files found. Move this python file to the folder that contains the PNG files to normalize.")
    sys.exit()

print(" ")
print(" -  %d PNG files were found at this folder (and subfolders)." % len(pngs))
print(" ")
while True:
    normalize = input(
        "[?] Do you want to normalize all images (Y/N)? ").lower()
    if len(normalize) > 0 and (normalize[0] == "y" or normalize[0] == "n"):
        break

normalized = 0
if normalize[0] == "y":
    for ipng in range(len(pngs)):
        perc = (float(ipng) / len(pngs)) * 100.0
        print("%.2f%% %s" % (perc, pngs[ipng]))
        if updatePNG(pngs[ipng]):
            normalized += 1
print(" ")
print("[+] %d PNG files were normalized." % normalized)
