#!/bin/bash

# Create the image cache directory
mkdir -p /var/www/html/motionLog
chmod a+rw /var/www/html/motionLog

# Execute the file, one pic every 2 seconds
python /usr/local/bin/seccam.py -m_sec 2.0 & > seccam.log 2> seccam.err

# Add the symlink
ln -s --relative /var/www/html/motionLog /var/www/html/app-dist/

# Allow client traffic for development
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

# Enable mod rewrite
/usr/sbin/a2enmod rewrite

# Make sure apache2 is running and rewrite is enabled
/etc/init.d/apache2 restart

# Run photo server
/usr/bin/nodejs photo-server.js > my_app_log.log 2> my_app_err.log &

while true; do
    sleep 300
done

# If execution reaches this point, the chute will stop running.
exit 0
