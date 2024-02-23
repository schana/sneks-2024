FROM public.ecr.aws/lambda/python:3.12

COPY requirements-scoring.txt .
RUN pypy -m pip install -r requirements-scoring.txt
RUN pypy -m pip install awslambdaric

COPY requirements.txt .
RUN pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"
ADD . "${LAMBDA_TASK_ROOT}"
