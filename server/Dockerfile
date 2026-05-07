FROM python:latest

WORKDIR /server

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY ./src .

CMD ["fastapi", "dev", "--host", "0.0.0.0"]