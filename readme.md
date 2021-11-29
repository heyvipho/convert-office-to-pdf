# Convert document to pdf

**Build docker:**

```
docker build --pull --rm -f "Dockerfile" -t convertdocument:latest "."

docker run -p 3000:3000 registry.gitlab.com/techcen/convert-office-to-pdf:conver-pdf

curl http://localhost:3000/convert?fileSrc=FILE_SRC
```
