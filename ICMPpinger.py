from socket import *
import os
import sys
import struct
import time
import select
import binascii

# By Jacob Duncan @ Salisbury University
# COSC 370 with Dr. Lu

ICMP_ECHO_REQUEST = 8

def checksum(string):
    # Creating the checksum of the packet
    string = bytearray(string)
    sum = 0
    upTo = (len(string) // 2) * 2

    for count in range(0, upTo, 2):
        thisVal = string[count+1] * 256 + string[count]
        sum = sum + thisVal
        sum = sum & 0xffffffff

    if upTo < len(string):
        sum = sum + string[-1]
        sum = sum & 0xffffffff

    sum = (sum >> 16) + (sum & 0xffff)
    sum = sum + (sum >> 16)
    result = ~sum
    result = result & 0xffff
    result = result >> 8 | (result << 8 & 0xff00)
    return result

def receiveOnePing(tempSocket, ID, timeout, dAddress):
    global rtt_min, rtt_max, rtt_sum, rtt_cnt
    # Being able to recieve the ping
    remaining = timeout
    while 1:
        start = time.time()
        ready = select.select([tempSocket], [], [], remaining)
        timeIn = (time.time() - start)
        # Timeout
        if ready[0] == []:
            return "Request has timed out"

        timeReceived = time.time()
        recPacket, addr = tempSocket.recvfrom(1024)

        icmpHeader = recPacket[20:28]
        icmpType, code, tempCheck, packetID, sequence = struct.unpack("bbHHh", icmpHeader)

        if type != 8 and packetID == ID:
            bytesIn = struct.calcsize("d")
            timeSent = struct.unpack("d", recPacket[28:28 + bytesIn])[0]
            rtt = (timeReceived - timeSent) * 1000
            rtt_cnt += 1
            rtt_sum += rtt
            rtt_min = min(rtt_min, rtt)
            rtt_max = max(rtt_max, rtt)
            return timeReceived - timeSent

        remaining = remaining - timeIn
        if remaining <= 0:
            return "Request has timed out"

def sendOnePing(tempSocket, dAddress, ID):
    # Being able to send the ping
    # Header is type (8), code (8), checksum (16), id (16), sequence (16)
    tempCheck = 0
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, tempCheck, ID, 1)
    data = struct.pack("d", time.time())
    tempCheck = checksum(header + data)

    if sys.platform == 'darwin':
        tempCheck = htons(tempCheck) & 0xffff
    else:
        tempCheck = htons(tempCheck)

    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, tempCheck, ID, 1)
    packet = header + data
    tempSocket.sendto(packet, (dAddress, 1)) 

def doOnePing(dAddress, timeout):
    # Sends out a single ping
    icmp = getprotobyname("icmp")
    #Creating Socket here
    tempSocket = socket(AF_INET, SOCK_DGRAM, icmp) 
    # Returns the current process of ID
    myID = os.getpid() & 0xFFFF
    # Sends one ping to the destination address
    sendOnePing(tempSocket, dAddress, myID)
    delay = receiveOnePing(tempSocket, myID, timeout, dAddress)
    # Closes the temporary socket made to ping
    tempSocket.close()
    print(delay)
    return delay

# Set timeout to 1 second, if response
# not given in 1 second, then timeout
def ping(host, timeout=1):

    # Global variables used to 
    # calculate min,max,avg packet
    # timings

    global rtt_min, rtt_max, rtt_sum, rtt_cnt
    rtt_min = float('+inf')
    rtt_max = float('-inf')
    rtt_sum = 0
    rtt_cnt = 0
    cnt = 0

    # Set destination to be the parameter "host" passed into
    # the function
    dest = gethostbyname(host)
    print ("Pinging " + dest + ":")
    print ("")
    arr = []

    while cnt < 10:
        cnt += 1
        arr.append(doOnePing(dest, timeout))
        time.sleep(1)

    if cnt != 0:
        print(" ")
        print("*** ", host, " ping stats ***")
        print("Packets transmitted  :", cnt)
        print("Packets received     :", rtt_cnt)
        packet_loss = 100.0 - rtt_cnt * 100.0 / cnt
        print("Packet loss          :", packet_loss, "%")
        print("Min RTT: ", format(min(arr), ".5f"), "seconds")
        print("Max RTT: ", format(max(arr), ".5f"), "seconds")
        print("Avg RTT: ", format(sum(arr)/10, ".5f"), "seconds")

def main():
    print("1. Ping localhost")
    print("2. Ping Google")
    print("3. Ping Cloudflare")
    print(" ")
    choice = int(input("Enter a number: "))
    print(" ")
    if choice == 1:
        print("Pining localhost 10 times!")
        ping("127.0.0.1")
    elif choice == 2:
        print("Pinging Google 10 times!")
        ping("8.8.8.8")
    elif choice == 3:
        print("Pinging Cloudflare 10 times!")
        ping("1.1.1.1")
    else:
        print("Not a valid choice!")

if __name__ == "__main__":
    main()
