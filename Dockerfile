# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.9
ARG ALPINE_VERSION=3.13
FROM python:${PYTHON_VERSION}-alpine${ALPINE_VERSION}

# Prevents Python from writing pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

# Keeps Python from buffering stdout and stderr to avoid situations where
# the application crashes without emitting any logs due to buffering.
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Create a non-privileged user that the app will run under.
# See https://docs.docker.com/go/dockerfile-user-best-practices/
ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    django-user

# Download dependencies as a separate step to take advantage of Docker's caching.

ARG DEV=false
COPY ./requirements.dev.txt /tmp/requirements.dev.txt
COPY ./requirements.txt /tmp/requirements.txt
RUN if [ $DEV = "true" ]; \
      then python -m pip install -r /tmp/requirements.dev.txt; \
      else python -m pip install -r /tmp/requirements.txt; \
    fi && \
    rm -r /tmp/

# Switch to the non-privileged user to run the application.
USER django-user

# Copy the source code into the container.
COPY ./app /app
WORKDIR /app

# Expose the port that the application listens on.
EXPOSE 8000

# Run the application.
CMD python manage.py runserver 0.0.0.0:8000
