FROM python:3.14-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 OSINTNET_DATA=/data
WORKDIR /app
COPY requirements.lock.txt ./
RUN pip install --no-cache-dir -r requirements.lock.txt && useradd -u 10001 -m osintnet && mkdir /data && chown osintnet /data
COPY osintnet ./osintnet
ARG GIT_REVISION=development
LABEL org.opencontainers.image.revision=$GIT_REVISION
ENV OSINTNET_REVISION=$GIT_REVISION
USER 10001
EXPOSE 8780
CMD ["uvicorn", "osintnet.app:app", "--host", "0.0.0.0", "--port", "8780", "--no-access-log"]
