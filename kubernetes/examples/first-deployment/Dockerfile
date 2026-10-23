FROM python:3.13-alpine
WORKDIR /srv
COPY public/ ./
ARG DEMO_VERSION=1.0.0
RUN sed -i "s/DEMO_VERSION/${DEMO_VERSION}/g" index.html
USER 65532:65532
EXPOSE 8080
CMD ["python", "-u", "-m", "http.server", "8080", "--bind", "0.0.0.0", "--directory", "/srv"]
