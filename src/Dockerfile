FROM python:3.10
ENV PYTHONUNBUFFERED 1

WORKDIR /zortenet_netapp

COPY requirements.txt requirements.txt
RUN apt-get update && apt-get install -y jq && apt-get clean
RUN pip install -r requirements.txt

RUN pip install --upgrade Flask
RUN pip install --upgrade evolved5g
RUN pip install --upgrade watchdog
RUN pip install --upgrade pyopenssl
RUN pip install --upgrade pyjwt

ADD . /zortenet_netapp
RUN mkdir capif_onboarding
#COPY src/api.py /zortenet_netapp/api.py
#COPY src/prepare.sh /zortenet_netapp/prepare.sh
#COPY src/capif_registration_template.json /zortenet_netapp/capif_registration_template.json
CMD ["sh", "/zortenet_netapp/prepare.sh"]

