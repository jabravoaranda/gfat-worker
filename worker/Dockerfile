FROM python:3.11

WORKDIR /usr/src/app
RUN pip install "gfatpy==0.14.13" 
COPY requirements.txt .
RUN pip install pip --upgrade
RUN pip install --user --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x start.sh

CMD ["./start.sh"]
