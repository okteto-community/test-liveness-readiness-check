# Alpine's BusyBox ships `wget`, so the healthcheck exec probe produces the exact
# same log line the customer sees: `wget: server returned error: HTTP/1.1 503 ...`
FROM python:3.12-alpine

WORKDIR /app
COPY app.py .

EXPOSE 8080
CMD ["python", "-u", "app.py"]
