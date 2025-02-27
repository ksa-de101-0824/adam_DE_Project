FROM python:3.12

WORKDIR /app
COPY . /app

RUN pip install -r requirements.txt

RUN mkdir /app

EXPOSE 8080

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
