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

# Apache site configuration
ADD chute/000-default.conf /etc/apache2/sites-available/

#  Get the web frontend
ADD chute/web /var/www/html

# Install files required by the chute.
#
# ADD <path_inside_repository> <path_inside_container>
#
ADD chute/seccam.py /usr/local/bin/seccam.py
ADD chute/run.sh /usr/local/bin/run.sh

# Set the work dir for nodejs photo server
WORKDIR "/var/www/html"

EXPOSE 80 81 8010

CMD ["/bin/bash", "/usr/local/bin/run.sh"]
