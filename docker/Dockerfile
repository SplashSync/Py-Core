FROM python:3.6-slim
WORKDIR /app

# Install required Libraries
RUN pip install pycryptodome crypto pysimplesoap peewee pytest

# Add Original Package Sources
ADD ./ /app/

# Install package as Editable
RUN pip install -e /app/

# Start Splash Python Server
CMD [ "python", "./splashpy/server.py", "--serve"]
# Start Python Console Only
#CMD [ "python", "-i"]

