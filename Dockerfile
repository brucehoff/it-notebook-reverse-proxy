FROM ubuntu:22.04
# notebook_type is jupyter or rstudio
ARG notebook_type=jupyter

# Update the repository sources list and install apache
RUN apt-get update && \
apt-get install -y python3-dev git unzip apache2 apache2-dev curl pip && apt-get clean

# patterned after https://github.com/Sage-Bionetworks-IT/packer-rstudio/blob/master/src/playbook.yaml#L76-L91
#       "The mod_python provided by apt in Ubuntu 22.04 intermittently fails with segmentation faults.
#       mod_python is only supported from master branch at https://github.com/grisha/mod_python.git"
ENV MOD_PYTHON_REPO_HASH=9db86bca5106b5cf7ceca7645ec0208446c71e25
RUN curl -o /archive.zip -L https://github.com/grisha/mod_python/archive/${MOD_PYTHON_REPO_HASH}.zip
RUN unzip /archive.zip
WORKDIR /mod_python-${MOD_PYTHON_REPO_HASH}
RUN ./configure --with-python=/usr/bin/python3
RUN make install
# add mod_python as an available module to enable later
RUN echo 'LoadModule python_module /usr/lib/apache2/modules/mod_python.so' >> /etc/apache2/mods-available/python.load


# Install Python dependencies
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Add JWT and instance tag verifying script
COPY access.py /usr/lib/cgi-bin/access.py
COPY access_helpers.py /usr/lib/cgi-bin/access_helpers.py

# Add config for local rev proxy to internal port
COPY ${notebook_type}_proxy.conf /etc/apache2/sites-available/proxy.conf

# Enable modules
RUN a2enmod ssl proxy proxy_http proxy_wstunnel rewrite python headers
# Enable proxy site
RUN a2ensite proxy
# Disable default
RUN a2dissite 000-default

COPY startup.sh /startup.sh

CMD /startup.sh
