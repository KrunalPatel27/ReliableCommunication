"""
Where solution code to HW5 should be written.  No other files should
be modified.
"""

import socket
import io
import time
import typing
import struct
import homework5
import homework5.logging


def send(sock: socket.socket, data: bytes):
    """
    Implementation of the sending logic for sending data over a slow,
    lossy, constrained network.

    Args:
        sock -- A socket object, constructed and initialized to communicate
                over a simulated lossy network.
        data -- A bytes object, containing the data to send over the network.
    """

    # Naive implementation where we chunk the data to be sent into
    # packets as large as the network will allow, and then send them
    # over the network, pausing half a second between sends to let the
    # network "rest" :)

    timeoutInterval = 1.0
    headerSize = 4
    logger = homework5.logging.get_logger("hw5-sender")
    chunk_size = homework5.MAX_PACKET - headerSize
    packetCount= 1
    pause = 2.0
    avgRTT = 0
    lastRTT = 0
    tripCount = 1
    sequenceNumber = 0
    offsets = range(0, len(data), chunk_size)
    for chunk in [data[i:i + chunk_size] for i in offsets]:
        sequenceNumber = packetCount * chunk_size
        packetCount = packetCount + 1
        chunk = struct.pack("i", sequenceNumber) + chunk
        sock.send(chunk)
        start = time.time()
        logger.info("Pausing for %f seconds", round(pause, 2))
        if packetCount != 2:
            pause = computeTimeout(avgRTT, lastRTT)
        sock.settimeout(pause)
        
        while True:
            try:
                data = sock.recv(headerSize)
                tempSequenceNumber = struct.unpack("i", data[:4])[0]
                if tempSequenceNumber == sequenceNumber:
                    lastRTT = time.time() - start
                    avgRTT = (( (tripCount -1) * avgRTT) + lastRTT)/(tripCount)
                    tripCount = tripCount + 1
                    break
            except:
                pause = computeTimeout((avgRTT+1.0), pause)
                sock.send(chunk)
                start = time.time()
                if packetCount == 2:
                    pause = 2.0
                sock.settimeout(pause)
        

def computeTimeout(avgRTT, lastRTT):
    return (0.8* avgRTT) + (.2*lastRTT)

def recv(sock: socket.socket, dest: io.BufferedIOBase) -> int:
    """
    Implementation of the receiving logic for receiving data over a slow,
    lossy, constrained network.

    Args:
        sock -- A socket object, constructed and initialized to communicate
                over a simulated lossy network.

    Return:
        The number of bytes written to the destination.
    """
    logger = homework5.logging.get_logger("hw5-receiver")
    # Naive solution, where we continually read data off the socket
    # until we don't receive any more data, and then return.
    num_bytes = 0
    sequenceNumber = 0
    while True:
        data = sock.recv(homework5.MAX_PACKET)
        if not data:
            break
        header = data[:4]
        data = data[4:]
        tempNumber = struct.unpack("i", header)[0]
        if data[4:] is b'':
            break
        
        logger.info("Received %d bytes", len(data))
        if tempNumber > sequenceNumber:
            sequenceNumber = tempNumber
            dest.write(data)
            num_bytes += len(data)
            dest.flush()
        sock.send(struct.pack("i", sequenceNumber))
    return num_bytes
