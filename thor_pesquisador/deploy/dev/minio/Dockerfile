FROM golang:1.24.8-alpine AS builder
RUN apk add --no-cache git ca-certificates
ENV CGO_ENABLED=0
RUN go install github.com/minio/minio@RELEASE.2025-10-15T17-29-55Z

FROM alpine:3.22
RUN apk add --no-cache ca-certificates && adduser -D -u 1001 app && mkdir /data && chown 1001:0 /data
COPY --from=builder /go/bin/minio /usr/local/bin/minio
USER 1001
EXPOSE 9000 9001
ENTRYPOINT ["minio"]
