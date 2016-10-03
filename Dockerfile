# Security Cam v2
#  - Fixed ip address webcam detecting motion
# Version 1.01.01
FROM ubuntu:14.04
#FROM debian:wheezy
MAINTAINER Paradrop Team <info@paradrop.io>

#RUN apt-get update
#sudo apt-get install nodejs

RUN apt-get update && apt-get install -y \
	apache2 \
	nodejs \
	python-imaging \
	&& apt-get clean \
	&& rm -rf /var/lib/apt/lists/*

#  Get the web frontend
#ADD http://paradrop.io/storage/seccam/srv.tar.gz /var/www/
#ADD http://paradrop.io/storage/seccam/srv.tar.gz /var/www/
ADD http://pages.cs.wisc.edu/~dmeyer/paradrop/seccam/seccam.tar.gz /var/www/
# Untar
#RUN tar xzf /var/www/srv.tar.gz -C /var/www/html/
RUN tar xzf /var/www/seccam.tar.gz -C /var/www/html/

# Remove the default apache2 index.html file
RUN echo "rm /var/www/html/index.html" >> /usr/local/bin/cmd.sh
# Enable the php5 cgi conf
#RUN echo "a2enconf php5-cgi" >> /usr/local/bin/cmd.sh
# Restart to enable the config
#RUN echo "/etc/init.d/apache2 restart" >> /usr/local/bin/cmd.sh

# Create the image cache directory
RUN echo "mkdir -p /var/www/html/motionLog" >> /usr/local/bin/cmd.sh
RUN echo "chmod a+rw /var/www/html/motionLog" >> /usr/local/bin/cmd.sh

# Get the main script file
ADD http://paradrop.io/storage/seccam/seccam_full_dmeyer.py /seccam_full.py
# Make the main python file executable
RUN echo "chmod +x /seccam_full.py" >> /usr/local/bin/cmd.sh

# Execute the file, one pic every 2 seconds
RUN echo "python /seccam_full.py -m_sec 2.0 &" >> /usr/local/bin/cmd.sh

# Run nodejs
RUN echo "/usr/bin/nodejs /var/www/html/photo-server.js &" >> /usr/local/bin/cmd.sh
# Add the symlink
RUN echo "ln -s --relative /var/www/html/motionLog /var/www/html/app-dist/" >> /usr/local/bin/cmd.sh

# Allow client traffic for development
RUN echo "iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE" >> /usr/local/bin/cmd.sh

RUN echo "while true; do sleep 421; done" >> /usr/local/bin/cmd.sh

CMD ["/bin/bash","/usr/local/bin/cmd.sh"]
