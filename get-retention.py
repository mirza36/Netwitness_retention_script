#!/usr/bin/env python

'''
Author: Naushad A Kasu naushad.kasu@rsa.com
Date: Jan 24, 2019
Comments: Help improve this script
'''

import sys
import os.path
import re
import subprocess
import shlex
from datetime import datetime, timedelta

class bcolors:
    OKBLUE = '\033[94m'
    BOLD = '\033[1m'
    ENDC = '\033[0m'
    
def calculateDaysRaw(rawDate, sessionDate, collection=None):
    rawDateConverted = datetime.strptime(rawDate.replace('[','').replace(']',''), '%Y-%b-%d %H:%M:%S')
    sessionDateConverted = datetime.strptime(rawDate.replace('[','').replace(']',''), '%Y-%b-%d %H:%M:%S')
    today = datetime.now()
    todayConverted = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    todayConverted = datetime.strptime(todayConverted, '%Y-%m-%d %H:%M:%S')
    
    # convert both into deltas from today's datetime
    rawDelta = str(todayConverted - rawDateConverted)
    sessionDelta = str(todayConverted - sessionDateConverted)

    print rawDelta

    # re-format our retention output
    daysRaw = rawDelta.split(',')[0].split(' ')[0]
    hoursRaw = rawDelta.split(',')[1].split(':')[0].strip()
    daysSession = sessionDelta.split(',')[0].split(' ')[0]
    hoursSession = sessionDelta.split(',')[1].split(':')[0].strip()

    if int(daysSession) <= int(daysRaw):
        if collection is None:
            print "Packet Oldest Time: %s\t\tRaw Retention: %s days %s hours" % (sessionDateConverted, daysSession, hoursSession)
        else:
            print "(collection: %s)\tPacket Oldest Time: %s\t\tRaw Retention: %s days %s hours" % (collection, sessionDateConverted, daysSession, hoursSession)
    else:
        if collection is None:
            print "Packet Oldest Time: %s\t\tRaw Retention: %s days %s hours" % (rawDateConverted, daysRaw, hoursRaw)
        else:
            print "(collection: %s)\tPacket Oldest Time: %s\t\tRaw Retention: %s days %s hours" % (collection, rawDateConverted, daysRaw, hoursRaw)

def calculateDaysMeta(indexDate, metaDate, sessionDate, collection=None):
    # convert index, session and meta date/time stamps into something we can work with
    indexDateConverted = datetime.strptime(indexDate.replace('[','').replace(']',''), '%Y-%b-%d %H:%M:%S')
    metaDateConverted = datetime.strptime(metaDate.replace('[','').replace(']',''), '%Y-%b-%d %H:%M:%S')
    sessionDateConverted = datetime.strptime(sessionDate.replace('[','').replace(']',''), '%Y-%b-%d %H:%M:%S')

    # get today's date
    today = datetime.now()
    todayConverted = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    todayConverted = datetime.strptime(todayConverted, '%Y-%m-%d %H:%M:%S')

    # convert both into deltas from today's datetime
    indexDelta = str(todayConverted - indexDateConverted)
    metaDelta = str(todayConverted - metaDateConverted)
    sessionDelta = str(todayConverted - sessionDateConverted)

    # re-format our retention output
    daysIndex = indexDelta.split(',')[0].split(' ')[0]
    hoursIndex = indexDelta.split(',')[1].split(':')[0].strip()
    daysSession = sessionDelta.split(',')[0].split(' ')[0]
    hoursSession = sessionDelta.split(',')[1].split(':')[0].strip()
    daysMeta = metaDelta.split(',')[0].split(' ')[0]
    hoursMeta = metaDelta.split(',')[1].split(':')[0].strip()

    if int(daysIndex) <= int(daysMeta) and int(daysIndex) <= int(daysSession):
        if collection is None:
            print "Meta Oldest Time: %s\t\tMeta Retention: %s days %s hours" % (indexDateConverted, daysIndex, hoursIndex)
        else:
            print "(collection: %s)\tMeta Oldest Time: %s\t\tMeta Retention: %s days %s hours" % (collection, indexDateConverted, daysIndex, hoursIndex)
    elif int(daysMeta) <= int(daysIndex) and int(daysMeta) <= int(daysSession):
        if collection is None:
            print "Meta Oldest Time: %s\t\tMeta Retention: %s days %s hours" % (metaDateConverted, daysMeta, hoursMeta)
        else:
            print "(collection: %s)\tMeta Oldest Time: %s\t\tMeta Retention: %s days %s hours" % (collection, metaDateConverted, daysMeta, hoursMeta)
    else:
        if collection is None:
            print "Meta Oldest Time: %s\t\tMeta Retention: %s days %s hours" % (sessionDateConverted, daysSession, hoursSession)
        else:
            print "(collection: %s)\tMeta Oldest Time: %s\t\tMeta Retention: %s days %s hours" % (collection, sessionDateConverted, daysSession, hoursSession)
    
def processType(host, ip, port, cert):

    if port == 56002 or port == 56004:
        try:
            cmd = "NwConsole -c tlogin server=" + ip + " port=" + str(port) + " username=admin group=Administrators cert=" + cert + " -c get /database/stats/packet.oldest.file.time"
            args = shlex.split(cmd)
            p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = p.communicate()
            rawDate = re.search("\[.*\]", out).group(0)
            
            cmd = "NwConsole -c tlogin server=" + ip + " port=" + str(port) + " username=admin group=Administrators cert=" + cert + " -c get /database/stats/session.oldest.file.time"
            args = shlex.split(cmd)
            p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = p.communicate()
            sessionDate = re.search("\[.*\]", out).group(0)
            
            calculateDaysRaw(rawDate, sessionDate)
        except:
            print "Error processing service. Please ensure there is a value for packet.oldest.file.time under View -> Explore -> database -> stats\n"
            pass
    if port == 56005:
        try:
            cmd = "NwConsole -c tlogin server=" + ip + " port=" + str(port) + " username=admin group=Administrators cert=" + cert + " -c get /index/stats/time.begin"
            args = shlex.split(cmd)
            p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = p.communicate()
            indexDate = re.search("\[.*\]", out).group(0)

            cmd = "NwConsole -c tlogin server=" + ip + " port=" + str(port) + " username=admin group=Administrators cert=" + cert + " -c get /database/stats/meta.oldest.file.time"
            args = shlex.split(cmd)
            p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = p.communicate()
            metaDate = re.search("\[.*\]", out).group(0)

            cmd = "NwConsole -c tlogin server=" + ip + " port=" + str(port) + " username=admin group=Administrators cert=" + cert + " -c get /database/stats/session.oldest.file.time"
            args = shlex.split(cmd)
            p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = p.communicate()
            sessionDate = re.search("\[.*\]", out).group(0)
 
            calculateDaysMeta(indexDate, metaDate, sessionDate)
        except:
            print "Error processing service. Please ensure there is a value for meta.oldest.file.time under View -> Explore -> database -> stats and time.begin under View -> Explore -> index -> stats\n"
            pass
    if port == 56008:

        # get a list of collections, Archivers work differently in that their database and index stats are not in their main REST path, but rather under their collections node under /archivers/collections/
        cmd = "NwConsole -c tlogin server=" + ip + " port=" + str(port) + " username=admin group=Administrators cert=" + cert + " -c cd /archiver/collections -c ls"
        args = shlex.split(cmd)
        p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        collections = re.findall("[a-zA-Z].*\/", out)

        try:
            for x in range(3, len(collections)):
                collection = collections[x].replace('/','')

                cmd = "NwConsole -c tlogin server=" + ip + " port=" + str(port) + " username=admin group=Administrators cert=" + cert + " -c get /archiver/collections/" + collection + "/database/stats/packet.oldest.file.time"
                args = shlex.split(cmd)
                p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                out, err = p.communicate()
                rawDate = re.search("\[.*\]", out).group(0)

                cmd = "NwConsole -c tlogin server=" + ip + " port=" + str(port) + " username=admin group=Administrators cert=" + cert + " -c get /archiver/collections/" + collection + "/database/stats/session.oldest.file.time"
                args = shlex.split(cmd)
                p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                out, err = p.communicate()
                rawDate = re.search("\[.*\]", out).group(0)

                calculateDaysRaw(rawDate, sessionDate, collection)

                cmd = "NwConsole -c tlogin server=" + ip + " port=" + str(port) + " username=admin group=Administrators cert=" + cert + " -c get /archiver/collections/" + collection + "/index/stats/time.begin"
                args = shlex.split(cmd)
                p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                out, err = p.communicate()
                indexDate = re.search("\[.*\]", out).group(0)

                cmd = "NwConsole -c tlogin server=" + ip + " port=" + str(port) + " username=admin group=Administrators cert=" + cert + " -c get /archiver/collections/" + collection + "/database/stats/meta.oldest.file.time"
                args = shlex.split(cmd)
                p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                out, err = p.communicate()
                metaDate = re.search("\[.*\]", out).group(0)

                cmd = "NwConsole -c tlogin server=" + ip + " port=" + str(port) + " username=admin group=Administrators cert=" + cert + " -c get /archiver/collections/" + collection + "/database/stats/session.oldest.file.time"
                args = shlex.split(cmd)
                p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                out, err = p.communicate()
                sessionDate = re.search("\[.*\]", out).group(0)

                calculateDaysMeta(indexDate, metaDate, sessionDate, collection)
        except:
            print "Error processing service. Please ensure there is a value for packet.oldest.file.time under View -> Explore -> archiver -> (collection i.e. default) -> database -> stats and time.begin under View -> Explore -> archiver -> (collection i.e. default) -> index -> stats\n"
            pass

'''
"main" logic
'''
def main():
    hosts = ''

    # read through the all-systems file
    if os.path.isfile("/var/netwitness/nw-backup/all-systems"):
        file = open('/var/netwitness/nw-backup/all-systems', 'r')
        hosts = file.read().rstrip().split('\n')
        cert = "/etc/pki/nw/node/node.pem"
    elif os.path.isfile("/var/netwitness/database/nw-backup/all-systems"):
        file = open('/var/netwitness/database/nw-backup/all-systems', 'r')
        hosts = file.read().rstrip().split('\n')
        cert = "/etc/netwitness/ng/broker_cert.pem"
    else:
        print "ERROR: Please run the appropriate ./get-all-systems.sh (v10 or v11) on this server before using this script."
        exit(0)

    # Service Types:
    #   EndpointLogHybrid = Log Decoder, Concentrator
    #   EndpointHybrid = Log Decoder, Concentrator
    #   Log Hybrid = Log Decoder, Concentrator
    #   IncLogDecoder = Log Decoder (indexing + compression)
    #   PacketHybrid = Decoder, Concentrator
    #   Concentrator = Concentrator
    #   Decoder = Decoder
    #   Log Decoder = Log Decoder
    #   Archiver = Archiver

    for host in hosts:
        if host.split(',')[0].lower() == 'endpointloghybrid' or host.split(',')[0].lower() == 'endpointhybrid' or host.split(',')[0].lower() == 'loghybrid':

            ip = host.split(',')[2]
            appliance = host.split(',')[0]
            host = host.split(',')[1]
            print bcolors.OKBLUE + bcolors.BOLD + "\nTYPE: " + bcolors.ENDC + bcolors.OKBLUE + appliance + bcolors.ENDC + bcolors.OKBLUE + bcolors.BOLD + " HOST: "  + bcolors.ENDC + bcolors.OKBLUE + host + bcolors.ENDC + bcolors.OKBLUE + bcolors.BOLD + " IP: " + bcolors.ENDC + bcolors.OKBLUE + ip + bcolors.ENDC
            processType(host, ip, 56002, cert)
            processType(host, ip, 56005, cert)

        elif host.split(',')[0].lower() == 'packethybrid' or host.split(',')[0].lower() == 'networkhybrid':

            ip = host.split(',')[2]
            appliance = host.split(',')[0]
            host = host.split(',')[1]
            print bcolors.OKBLUE + bcolors.BOLD + "\nTYPE: " + bcolors.ENDC + bcolors.OKBLUE + appliance + bcolors.ENDC + bcolors.OKBLUE + bcolors.BOLD + " HOST: "  + bcolors.ENDC + bcolors.OKBLUE + host + bcolors.ENDC + bcolors.OKBLUE + bcolors.BOLD + " IP: " + bcolors.ENDC + bcolors.OKBLUE + ip + bcolors.ENDC
            processType(host, ip, 56004, cert)
            processType(host, ip, 56005, cert)

        elif host.split(',')[0].lower() == 'concentrator':

            ip = host.split(',')[2]
            appliance = host.split(',')[0]
            host = host.split(',')[1]
            print bcolors.OKBLUE + bcolors.BOLD + "\nTYPE: " + bcolors.ENDC + bcolors.OKBLUE + appliance + bcolors.ENDC + bcolors.OKBLUE + bcolors.BOLD + " HOST: "  + bcolors.ENDC + bcolors.OKBLUE + host + bcolors.ENDC + bcolors.OKBLUE + bcolors.BOLD + " IP: " + bcolors.ENDC + bcolors.OKBLUE + ip + bcolors.ENDC
            processType(host, ip, 56004, cert)
            processType(host, ip, 56005, cert)

        elif host.split(',')[0].lower() == 'decoder' or host.split(',')[0].lower() == 'networkdecoder' or host.split(',')[0].lower() == 'network decoder':

            ip = host.split(',')[2]
            appliance = host.split(',')[0]
            host = host.split(',')[1]
            print bcolors.OKBLUE + bcolors.BOLD + "\nTYPE: " + bcolors.ENDC + bcolors.OKBLUE + appliance + bcolors.ENDC + bcolors.OKBLUE + bcolors.BOLD + " HOST: "  + bcolors.ENDC + bcolors.OKBLUE + host + bcolors.ENDC + bcolors.OKBLUE + bcolors.BOLD + " IP: " + bcolors.ENDC + bcolors.OKBLUE + ip + bcolors.ENDC
            processType(host, ip, 56004, cert)

        elif host.split(',')[0].lower() == 'log decoder' or host.split(',')[0].lower() == 'logdecoder' or host.split(',')[0].lower() == 'inclogdecoder':

            ip = host.split(',')[2]
            appliance = host.split(',')[0]
            host = host.split(',')[1]
            print bcolors.OKBLUE + bcolors.BOLD + "\nTYPE: " + bcolors.ENDC + bcolors.OKBLUE + appliance + bcolors.ENDC + bcolors.OKBLUE + bcolors.BOLD + " HOST: "  + bcolors.ENDC + bcolors.OKBLUE + host + bcolors.ENDC + bcolors.OKBLUE + bcolors.BOLD + " IP: " + bcolors.ENDC + bcolors.OKBLUE + ip + bcolors.ENDC
            processType(host, ip, 56002, cert)

        elif host.split(',')[0].lower() == 'archiver':

            ip = host.split(',')[2]
            appliance = host.split(',')[0]
            host = host.split(',')[1]
            print bcolors.OKBLUE + bcolors.BOLD + "\nTYPE: " + bcolors.ENDC + bcolors.OKBLUE + appliance + bcolors.ENDC + bcolors.OKBLUE + bcolors.BOLD + " HOST: "  + bcolors.ENDC + bcolors.OKBLUE + host + bcolors.ENDC + bcolors.OKBLUE + bcolors.BOLD + " IP: " + bcolors.ENDC + bcolors.OKBLUE + ip + bcolors.ENDC
            processType(host, ip, 56008, cert)

        else:
            pass

'''
Kickoff script
'''
if __name__ == "__main__":
    main()

