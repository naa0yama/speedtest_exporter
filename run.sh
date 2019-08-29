docker run \
  -d \
  --name=grafana.speedtest \
  -p 9353:9353 \
  wildme/speedtest:latest --server "random" --interval "*/15 * * * *"

