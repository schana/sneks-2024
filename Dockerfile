FROM public.ecr.aws/lambda/python:3.12 AS build

COPY . /tmp/sneks
RUN pip install "/tmp/sneks[extra,record]"


FROM public.ecr.aws/lambda/python:3.12

COPY --from=build ${LAMBDA_TASK_ROOT} ${LAMBDA_TASK_ROOT}
