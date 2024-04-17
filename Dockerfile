FROM python:3.11
ENV PYTHONPATH "${PYTHONPATH}:/app"
ENV PATH "/app/:${PATH}"
WORKDIR /app

# Install dependencies
RUN apt-get install libcairo2-dev pkg-config
RUN pip install wheel
COPY requirements.txt /app/
RUN pip install -r requirements.txt

# Prepare entrypoint
ADD . /app/
RUN chmod +x run.sh
ENTRYPOINT ["run.sh"]