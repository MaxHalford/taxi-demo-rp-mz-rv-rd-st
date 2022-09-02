FROM python:3.8-slim
ADD requirements.txt /
RUN pip install -r requirements.txt
ADD run.py /
CMD ["python", "-u", "./run.py", "--speed", "10"]
