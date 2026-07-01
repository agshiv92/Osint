FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Streamlit headless config for Cloud Run
RUN mkdir -p /app/.streamlit && \
    printf '[server]\nheadless = true\nport = 8080\naddress = "0.0.0.0"\nenableCORS = false\nenableXsrfProtection = false\n\n[browser]\ngatherUsageStats = false\n' > /app/.streamlit/config.toml

EXPOSE 8080

CMD ["streamlit", "run", "app.py"]
