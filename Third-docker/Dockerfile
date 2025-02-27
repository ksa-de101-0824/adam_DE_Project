FROM ubuntu:22.04

WORKDIR /app

COPY . /app

RUN apt-get update && apt-get install -y python3 python3-pip
RUN pip3 install fastapi uvicorn python-multipart

#within directory, make a new directory called data
RUN mkdir /data 

#define data as a volume
VOLUME /data

#expose port 8080
EXPOSE 8080

#run fastapi using uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]