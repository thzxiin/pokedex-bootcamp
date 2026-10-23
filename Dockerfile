FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HOST=0.0.0.0 PORT=8000 DB_PATH=/app/data/pokedex.sqlite3
RUN useradd --create-home appuser && mkdir -p /app/data && chown appuser:appuser /app/data
COPY --chown=appuser:appuser app.py ./
COPY --chown=appuser:appuser static ./static
USER appuser
VOLUME ["/app/data"]
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=3)" || exit 1
CMD ["python", "app.py"]
