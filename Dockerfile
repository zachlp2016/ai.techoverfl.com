FROM python:3.12-slim

WORKDIR /app
COPY site/ /app/

EXPOSE 8080
CMD ["python", "server.py"]
