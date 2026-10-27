FROM python:3.13-slim
WORKDIR /executor
COPY apps/api/app/sandbox_runner.py /executor/run.py
USER 65532:65532
ENTRYPOINT ["python","-I","/executor/run.py"]
