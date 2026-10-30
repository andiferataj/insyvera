FROM golang:1.24-alpine AS build
RUN apk add --no-cache ca-certificates git
WORKDIR /src
# Preserve the release previously used by Compose; verify the full source commit.
RUN git init . \
    && git fetch --depth=1 https://github.com/minio/minio.git 07c3a429bfed433e49018cb0f78a52145d4bedeb \
    && git checkout --detach FETCH_HEAD \
    && test "$(git rev-parse HEAD)" = "07c3a429bfed433e49018cb0f78a52145d4bedeb"
ENV CGO_ENABLED=0
RUN go mod download
RUN go build -trimpath -tags kqueue -o /out/minio .
RUN /out/minio --version

FROM alpine:3.22
RUN apk add --no-cache ca-certificates \
    && addgroup -g 10001 minio \
    && adduser -D -u 10001 -G minio minio \
    && mkdir -p /data \
    && chown minio:minio /data
COPY --from=build /out/minio /usr/local/bin/minio
COPY --from=build /src/LICENSE /usr/share/licenses/minio/LICENSE
ENV MINIO_UPDATE=off
USER 10001:10001
EXPOSE 9000 9001
ENTRYPOINT ["minio"]
CMD ["server", "/data", "--console-address", ":9001"]
