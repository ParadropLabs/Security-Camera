#!/usr/bin/python

import sys, math, os, string, time, argparse, json, subprocess
import httplib
import base64
import StringIO

try:
    import PIL
    from PIL import Image, ImageChops
except Exception as e:
    print('No PIL, please install "python-imaging-library" if on OpenWrt')
    sys.exit(1)

timeflt = lambda: time.time()

THRESH_0 = 20.0
THRESH_1 = 40.0
THRESH_2 = 60.0

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
        print "return code:",returncode
        print "return message:",returnmsg
        print "headers:",headers
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
        jpg1 = PIL.Image.open(img1)
    except Exception as e:
        print('jpg1: %s' % str(e))
        return None

    if(not jpg2):
        return (None, jpg1)

    # Now compute the difference
    diff = PIL.ImageChops.difference(jpg1, jpg2)
    h = diff.histogram()
    sq = (value*((idx%256)**2) for idx, value in enumerate(h))
    sum_sqs = sum(sq)
    rms = math.sqrt(sum_sqs / float(jpg1.size[0] * jpg1.size[1]))
    return (rms,jpg1)



if(__name__ == "__main__"):
    p = setupArgParse()
    args = p.parse_args()

    calib = args.calibrate
    m_sec = args.m_sec
    sens = args.m_sensitivity
    m_save = '/var/www/html/motionLog/motion-'

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

    ## Determine IP address
    #######################################################################
    # make sure apr table contains all devices
    # Get the subnet of paradrop
    subnet = ""
    ip = ""
    while(ip == ""):
        try:

            # Get the subnet if haven't yet
            if (subnet == ""):
                cmd = "ifconfig -a | grep 'inet addr:192.168' | awk '{print $2}' | egrep -o '([0-9]+\.){2}[0-9]+'"
                p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
                output, errors = p.communicate()
                if (output != ""):
                    subnet = output.rstrip()

                    # Add a . after 192.168.xxx
                    subnet = subnet + '.'
                    print "subnet: " + subnet

            # Prevent race condition by running this in the loop to put the device on the arp table
            cmd = "echo $(seq 100 200) | xargs -P255 -I% -d' ' ping -W 1 -c 1 " + subnet + "% | grep -E '[0-1].*?:'"
            p2 = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
            output2, errors2 = p2.communicate()

            # Search arp for leading mac address bits
            cmd="arp -a | grep -e '28:10:7b' -e 'b0:c5:54' -e '01:b0:c5' | awk '{print $2}' | egrep -o '([0-9]+\.){3}[0-9]+'"
            p3 = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
            output3, errors3 = p3.communicate()

            if (output3 != ""):
                print "output3: '" + output3 + "'"
                ip = output3.rstrip()

                # Set iptables for wan port access
                cmd="iptables -t nat -A PREROUTING -p tcp --dport 81 -j DNAT --to-destination " + ip + ":80"
                print "cmd: " + cmd
                p4 = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
                output4, errors4 = p4.communicate()
                cmd="iptables -t nat -A POSTROUTING -p tcp -d " + ip + " --dport 81 -j MASQUERADE"
                print "cmd: " + cmd
                p5 = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
                output5, errors5 = p5.communicate()

        except KeyboardInterrupt:
            break
        except Exception as e:
            print('!! error: %s' % str(e))
            time.sleep(m_sec)

    print("Found IP %s" % ip)

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
