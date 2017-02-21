#!/usr/bin/python

import argparse
import base64
import httplib
import math
import operator
import os
import re
import StringIO
import subprocess
import sys
import thread
import time

from flask import Flask, jsonify, send_from_directory
from PIL import Image, ImageChops


THRESH_0 = 20.0
THRESH_1 = 40.0
THRESH_2 = 60.0

WIFI_LEASE = "/paradrop/dnsmasq-wifi.leases"
CAMERA_MAC = os.environ.get('CAMERA_MAC')
CAMERA_HOSTNAME = os.environ.get('CAMERA_HOSTNAME')
PARADROP_DATA_DIR = os.environ.get("PARADROP_DATA_DIR", "/tmp")
PARADROP_SYSTEM_DIR = os.environ.get("PARADROP_SYSTEM_DIR", "/tmp")

PHOTO_NAME_RE = re.compile(r"motion-(.*)\.jpg")
SAVE_DIR = os.path.join(PARADROP_DATA_DIR, "motionLog")
MAX_LATEST = 40

server = Flask(__name__)


def setupArgParse():
    p = argparse.ArgumentParser(description='SecCam security suite')
    p.add_argument('-calibrate', help='Temporary mode to help calibrate the thresholds', action='store_true')
    p.add_argument('-m_sec', help='How much time to wait between motion images', type=float, default=2.0)
    p.add_argument('-m_sensitivity', help='How sensitive the motion capture should be, 0=very, 1=somewhat, 2=not very', type=int, default=0)
    return p


def getImage(ip):
    """Gets the file from the specified host, port and location/query"""
    try:
        # Here is a portion of the URL
        #######################################################################
        # TODO1 : Send a HTTP GET Request to the WebCam
        # (with Username:'admin' and Password:'').
        # We recommend using the httplib package
        h = httplib.HTTP(ip, 80)
        h.putrequest('GET', '/image.jpg')
        h.putheader('Host', ip)
        h.putheader('User-agent', 'python-httplib')
        h.putheader('Content-type', 'image/jpeg')
        h.putheader('Authorization', 'Basic {0}'.format(base64.b64encode("{0}:".format('admin'))))
        h.endheaders()

        (returncode, returnmsg, headers) = h.getreply()
        if returncode != 200:
            print returncode, returnmsg
            sys.exit()

        f = h.getfile()
        return StringIO.StringIO(f.read())

    except Exception as e:
        print('!! Failed to connect to webcam: %s' % str(e))
        return None


def detectMotion(img1, jpg2):
    """
            Detects motion using a simple difference algorithm.
            Arguments:
                    img1 : the image data from the getImage() function
                    jpg2 : the last jpg object (you save outside of this function)
            Returns:
                    None if no img data provided
                    (None, JPG) if jpg2 is None, we convert img1 into a JPG object and return that
                    (RMS, JPG) if img difference successful
    """
    if(not img1):
        return None

    #Convert to Image so we can compare them using PIL
    try:
        jpg1 = Image.open(img1)
    except Exception as e:
        print('jpg1: %s' % str(e))
        return None

    if(not jpg2):
        return (None, jpg1)

    # Now compute the difference
    diff = ImageChops.difference(jpg1, jpg2)
    h = diff.histogram()
    sq = (value*((idx%256)**2) for idx, value in enumerate(h))
    sum_sqs = sum(sq)
    rms = math.sqrt(sum_sqs / float(jpg1.size[0] * jpg1.size[1]))
    return (rms,jpg1)


def getCameraIP():
    """
            Checks the paradrop wifi lease file for the camera's IP address
            Arguments:
                    None.
            Returns:
                    IP address of the camera
    """
    ip = ""
    while(ip == ""):
        try:

            # Check for the file existing
            if (os.path.isfile(WIFI_LEASE)):
                with open(WIFI_LEASE) as f:
                    for line in f:

                        # Example lease line:
                        #    1479277513 b0:c5:54:13:80:86 192.168.128.181 DCS-931L 01:b0:c5:54:13:80:86
                        time,mac,ipaddr,hostname,altmac = line.split()

                        # Check environment variables
                        if ( CAMERA_MAC ):
                            print "Camera_mac exists: " + CAMERA_MAC
                            if( mac == CAMERA_MAC ):
                                ip = ipaddr
                        elif ( CAMERA_HOSTNAME ):
                            print "Camera_hostname exists: " + CAMERA_HOSTNAME
                            if( hostname == CAMERA_HOSTNAME ):
                                ip = ipaddr

                        # Check the known D-Link camera macs we have for the workshop
                        elif '28:10:7b' in mac:
                            print "28:10:7b exists "
                            ip = ipaddr
                        elif 'b0:c5:54' in mac:
                            print "b0:c5:54 exists "
                            ip = ipaddr
                        elif '01:b0:c5' in mac:
                            print "01:b0:c5 exists "
                            ip = ipaddr

        except KeyboardInterrupt:
            break
        except Exception as e:
            print('!! error: %s' % str(e))
            time.sleep(m_sec)
    return ip


@server.route('/motionLog/<path:path>')
def GET_motionLog(path):
    return send_from_directory(SAVE_DIR, path)


@server.route('/photos')
def GET_photos():
    photos = []
    for fname in os.listdir(SAVE_DIR):
        match = PHOTO_NAME_RE.match(fname)
        if match is None:
            continue

        ts = match.group(1)
        try:
            ts = float(ts)
        except ValueError:
            pass

        photos.append({
            'path': os.path.join('motionLog', fname),
            'ts': ts
        })

    photos.sort(key=operator.itemgetter('ts'), reverse=True)
    return jsonify(photos[:MAX_LATEST])


@server.route('/')
def GET_root():
    return send_from_directory('web/app-dist', 'index.html')


@server.route('/<path:path>')
def GET_dist(path):
    return send_from_directory('web/app-dist', path)


if(__name__ == "__main__"):
    # Make sure the photo directory exists.
    if not os.path.isdir(SAVE_DIR):
        os.makedirs(SAVE_DIR)

    # Run the web server in a separate thread.
    thread.start_new_thread(server.run, (), {'host': '0.0.0.0'})

    p = setupArgParse()
    args = p.parse_args()

    calib = args.calibrate
    m_sec = args.m_sec
    sens = args.m_sensitivity
    m_save = os.path.join(SAVE_DIR, "motion-")

    if(m_sec < 1.0):
        print('** For the workshop, please do not use lower than 1.0 for m_sec')
        exit()

    #Setup threshold for motion
    #very sensitive
    if(sens == 0):
        thresh = THRESH_0
    #kind of sensitive
    elif(sens == 1):
        thresh = THRESH_1
    #not very sensitive
    elif(sens == 2):
        thresh = THRESH_2
    else:
        raise Exception('InvalidParam', 'm_sensitivity')

    # Need to store the old image
    oldjpg = None


    ip = getCameraIP()
    print("Found IP %s" % ip)

    # Set iptables for wan port access
    cmd="iptables -t nat -A PREROUTING -p tcp --dport 81 -j DNAT --to-destination " + ip + ":80"
    print "cmd: " + cmd
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    output, errors = p.communicate()
    cmd="iptables -t nat -A POSTROUTING -p tcp -d " + ip + " --dport 81 -j MASQUERADE"
    print "cmd: " + cmd
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    output, errors = p.communicate()

    # Setup while loop requesting images from webcam
    while(True):
        try:
            img = getImage(ip)
            # Did we get an image?
            if(img is None):
                print("** No image discovered")
                time.sleep(m_sec)
                continue
            else:
                tup = detectMotion(img, oldjpg)
                if(tup):
                    # Explode the result
                    diff, jpg = tup
                    if(calib):
                        print(diff)
                    elif(diff):
                        # if above a threshold, store it to file
                        #######################################################################
                        # TODO2 : Check the RMS difference and store the image to the proper
                        # location, for our webserver to read these files they should go
                        # under the location /srv/www/motionlog/* 
                        if(diff > thresh):
                            print("** Motion! %.3f" % diff)
                            fileName = "%s%d.jpg" % (m_save, time.time())
                            jpg.save(fileName)
                    else:
                        print('-- No diff yet')
                    oldjpg = jpg
            time.sleep(m_sec)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print('!! error: %s' % str(e))
            time.sleep(m_sec)
