FROM python:3.9-alpine

WORKDIR /app

COPY . .

ARG PIP_NO_CACHE_DIR=1
ARG PIP_DISABLE_PIP_VERSION_CHECK=1
ARG PIP_ROOT_USER_ACTION=ignore

RUN pip install -r requirements.txt

CMD ["python", "main.py"]