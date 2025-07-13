FROM python:3.12.4

RUN apt-get update && apt-get install -y --no-install-recommends \
        curl ca-certificates bash           \
    && rm -rf /var/lib/apt/lists/*

RUN pip install streamlit requests

# 2. Copy code *first* to leverage Docker cache
WORKDIR /app

COPY streamlit_app.py  /app/

ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_PORT=8501
EXPOSE 8501

CMD ["streamlit", "run", "streamlit_app.py"]
