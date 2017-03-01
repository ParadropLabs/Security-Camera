# Security Cam for Paradrop

Security Camera Chute

## Catagory: Security, Computer Vision

Requirements:
* Wireless security cam that can connect to the Paradrop router.

## Description:

A motion detection system using a webcam to capture differing images.  Everything is kept within the router, with nothing getting sent to the cloud.

## Files

* Dockerfile: Uses apache2, nodejs, python-imaging, iptables
* seccam.py: Takes in three arguments for caliberation, time and sensitivity. According to these parameter, the security camera takes pictures each time it [detects motion](https://pillow.readthedocs.io/en/3.0.0/_modules/PIL/ImageChops.html) and saves it on the router for future reference.
* run.sh

## Getting Started

1. Fork this project to your own github account.
2. seccamp.py is the main file where the functionality of motion detection lies. [httplib](https://docs.python.org/2/library/httplib.html) is used for getting the file handle.
3. Change the run.sh for tweaking the parameters.

When creating a version of this chute, you should configure it as
shown in the image.  Your camera will be pre-configured to connect to a
certain ESSID, which you should enter in the form.  You will be given
this information during the workshop.  Also, be sure to add the port
binding and web service port as shown.

![Create version options](/images/create_version.png)

