FROM golang:1.17-alpine

WORKDIR /app

RUN apk add libreoffice \
	build-base \ 
	# Install fonts
	msttcorefonts-installer fontconfig && \
    update-ms-fonts && \
    fc-cache -f

RUN apk add --no-cache build-base libffi libffi-dev

COPY go.mod ./
RUN go mod download

COPY *.go ./

RUN go build -o /build

EXPOSE 3000

CMD [ "/build" ]