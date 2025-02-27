FROM ubuntu:22.04
WORKDIR /app
COPY . /app
RUN apt-get update && apt-get install -y python3 python3-pip
RUN pip3 install fastapi uvicorn
EXPOSE 8080
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
