FROM python:3.12-slim

WORKDIR /app
COPY site/ /app/

RUN useradd --create-home --uid 10001 dashboard
USER dashboard

EXPOSE 8080
CMD ["python", "server.py"]
