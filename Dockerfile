# Security Cam v2
#  - Finds ip address webcam - used for detecting motion
# Version 1.10.00
#FROM ubuntu:14.04
FROM dmeyer-seccam-img
#FROM debian:wheezy
MAINTAINER Paradrop Team <info@paradrop.io>

# Install required packages
RUN apt-get update && apt-get install -y \
	apache2 \
	iptables \
	nodejs \
	python-imaging \
	&& apt-get clean \
	&& rm -rf /var/lib/apt/lists/*

#  Get the web frontend
ADD http://pages.cs.wisc.edu/~dmeyer/paradrop/seccam/seccam.tar.gz /var/www/
#ADD chute/seccam_web.tar.gz /var/www/
# Untar
#RUN tar xzf /var/www/seccam_web.tar.gz -C /var/www/html/
RUN tar xzf /var/www/seccam.tar.gz -C /var/www/html/

# Remove the default apache2 index.html file
RUN echo "rm /var/www/html/index.html" >> /usr/local/bin/cmd.sh

# Create the image cache directory
RUN echo "mkdir -p /var/www/html/motionLog" >> /usr/local/bin/cmd.sh
RUN echo "chmod a+rw /var/www/html/motionLog" >> /usr/local/bin/cmd.sh

# Get the main script file
#ADD http://paradrop.io/storage/seccam/seccam_full_dmeyer.py /seccam_full.py
ADD chute/seccam.py /seccam.py
# Make the main python file executable
RUN echo "chmod +x /seccam.py" >> /usr/local/bin/cmd.sh

# Execute the file, one pic every 2 seconds
RUN echo "python /seccam.py -m_sec 2.0 & > seccam.log 2> seccam.err" >> /usr/local/bin/cmd.sh

# Add the symlink
RUN echo "ln -s --relative /var/www/html/motionLog /var/www/html/app-dist/" >> /usr/local/bin/cmd.sh

# Allow client traffic for development
RUN echo "iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE" >> /usr/local/bin/cmd.sh

# Make sure apache2 is running
RUN echo "/etc/init.d/apache2 restart" >> /usr/local/bin/cmd.sh

# Set the work dir for nodejs photo server
WORKDIR "/var/www/html"

EXPOSE 5000

# Run photo server
RUN echo "/usr/bin/nodejs photo-server.js > my_app_log.log 2> my_app_err.log &" >> /usr/local/bin/cmd.sh
RUN echo "while true; do sleep 421; done" >> /usr/local/bin/cmd.sh

CMD ["/bin/bash","/usr/local/bin/cmd.sh"]
