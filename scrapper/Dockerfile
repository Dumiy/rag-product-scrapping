FROM python:3.11-bookworm
WORKDIR ./scrapper
RUN apt-get update && apt install -y cmake
RUN pip install --upgrade pip
COPY requirements.txt requirements.txt
RUN pip3 install onnxruntime
RUN pip install -r requirements.txt
EXPOSE 5001
COPY . .
CMD ["fastapi", "dev", "app.py", "--host", "0.0.0.0", "--port",  "5001"]