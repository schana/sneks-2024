FROM public.ecr.aws/lambda/python:3.12-arm64 AS build

COPY . /tmp/sneks
RUN pip install "/tmp/sneks[extra,record]" --target ${LAMBDA_TASK_ROOT}


FROM public.ecr.aws/lambda/python:3.12-arm64

COPY --from=build ${LAMBDA_TASK_ROOT} ${LAMBDA_TASK_ROOT}
