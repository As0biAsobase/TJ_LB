FROM python:3

WORKDIR /usr/tj_lb

COPY ./src ./
COPY requirements.txt ./

RUN pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir -r requirements.txt
