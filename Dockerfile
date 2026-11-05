FROM mcr.microsoft.com/playwright/python:v1.64.1-noble

USER root

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HEADLESS=true \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /work

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && python -m playwright install chromium

COPY . .
RUN mkdir -p /work/reports

CMD ["pytest", "-n", "2", "--html=reports/report.html", "--self-contained-html"]
