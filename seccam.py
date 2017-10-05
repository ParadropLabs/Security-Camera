#!/usr/bin/python
from __future__ import print_function

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
from pdtools import ParadropClient


MOTION_THRESHOLD = os.environ.get('MOTION_THRESHOLD', 40.0)
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
    return p


def detectMotion(img1, img2):
    """
            Detects motion using a simple difference algorithm.
            Arguments:
                    img1 : the image from the getImage() function
                    img2 : the previous image
            Returns:
                    RMS if img difference success
                    None otherwise
    """
    if(not img1):
        return None

    # Now compute the difference
    diff = ImageChops.difference(img1, img2)
    h = diff.histogram()
    sq = (value*((idx%256)**2) for idx, value in enumerate(h))
    sum_sqs = sum(sq)
    rms = math.sqrt(sum_sqs / float(img1.size[0] * img1.size[1]))
    return rms


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
    m_save = os.path.join(SAVE_DIR, "motion-")

    if(m_sec < 1.0):
        print('** For the workshop, please do not use lower than 1.0 for m_sec')
        exit()

    try:
        thresh = float(MOTION_THRESHOLD)
    except ValueError:
        raise Exception("MOTION_THRESHOLD is not numeric")

    client = ParadropClient()

    # Wait until we detect at least one camera.
    cameras = []
    while len(cameras) < 1:
        time.sleep(m_sec)
        cameras = client.get_cameras()

    for camera in cameras:
        # Set iptables for wan port access
        cmd="iptables -t nat -A PREROUTING -p tcp --dport 81 -j DNAT --to-destination " + camera.host + ":80"
        print("cmd: " + cmd)
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        output, errors = p.communicate()
        cmd="iptables -t nat -A POSTROUTING -p tcp -d " + camera.host + " --dport 81 -j MASQUERADE"
        print("cmd: " + cmd)
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        output, errors = p.communicate()

    prev_images = dict()
    while True:
        # Getting the list of cameras every iteration in case a camera connects
        # or disconnects.
        for camera in client.get_cameras():
            try:
                img = camera.get_image()
            except Exception as error:
                print("Error getting image from {}: {}".format(camera, str(error)))
                continue

            if img is None:
                print("** No image returned from {}".format(camera))
                continue

            # Load into Image object so we can compare images using PIL
            try:
                img = Image.open(img)
            except Exception as error:
                print("Image: {}".format(str(error)))
                continue

            if camera.host in prev_images:
                diff = detectMotion(img, prev_images[camera.host])
                if calib:
                    print(diff)
                elif diff:
                    # if above a threshold, store it to file
                    if diff > thresh:
                        print("** Motion! {:.3f}".format(diff))
                        fileName = "%s%d.jpg" % (m_save, time.time())
                        img.save(fileName)
                else:
                    print('-- No diff yet')

            else:
                print("Processed first image from {}".format(camera))

            prev_images[camera.host] = img

        time.sleep(m_sec)
