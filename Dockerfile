# Security Cam v2
#  - Finds ip address webcam - used for detecting motion
# Version 1.10.00
FROM paradrop/workshop
MAINTAINER Paradrop Team <info@paradrop.io>

# Install dependencies.  You can add additional packages here following the example.
RUN apt-get update && apt-get install -y \
#	<package> \
	apache2 \
	iptables \
	nodejs \
	python-imaging \
	&& apt-get clean \
	&& rm -rf /var/lib/apt/lists/*

#  Get the web frontend
#ADD http://pages.cs.wisc.edu/~dmeyer/paradrop/seccam/seccam.tar.gz /var/www/
ADD chute/web /var/www/html
# Untar
#RUN tar xzf /var/www/seccam_web.tar.gz -C /var/www/html/
#RUN tar xzf /var/www/seccam.tar.gz -C /var/www/html/

# Remove the default apache2 index.html file
RUN rm /var/www/html/index.html

# Install files required by the chute.
#
# ADD <path_inside_repository> <path_inside_container>
#
#ADD http://paradrop.io/storage/seccam/seccam_full_dmeyer.py /seccam_full.py
ADD chute/seccam.py /usr/local/bin/seccam.py
ADD chute/run.sh /usr/local/bin/run.sh

# Set the work dir for nodejs photo server
WORKDIR "/var/www/html"

EXPOSE 80

CMD ["/bin/bash", "/usr/local/bin/run.sh"]
