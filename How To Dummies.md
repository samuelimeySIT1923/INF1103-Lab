git init [Initialise git repository]
git status [Check Repo status]

Every Segment Done:
git add {file name}.py
git commit -m "{Insert Commit Name}"
git log [View History]
git push [Send to GitHub]

Once Fully done:
docker run --rm -it -v "${PWD}:/usr/src/app" -w /usr/src/app python:3.11-slim python {FileName}.py

> Docker file contents:
FROM python:3.11-slim
WORKDIR /app
COPY {FileName}.py .
CMD ["python", "{FileName}.py"]

docker build -t {Name of image file (eg inf1103-labs-filename)} .
docker run --rm -it {Name of image file (eg inf1103-labs-filename)}

docker images [Show successfully built image]
