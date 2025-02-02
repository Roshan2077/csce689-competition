# Base image using Micromamba for managing Python dependencies
FROM mambaorg/micromamba:0.25.1 as ember

USER root
WORKDIR /ember

# Set environment variables for Mamba
ENV MAMBA_ROOT_PREFIX=/opt/mamba
ENV CONDA_PKGS_DIRS=$MAMBA_ROOT_PREFIX/pkgs
ENV MAMBA_EXE=/bin/micromamba
ENV MAMBA_NO_BANNER=1
ENV PATH /opt/mamba/bin:$PATH

# Create the directory for Mamba and ensure it is writable
RUN mkdir -p $MAMBA_ROOT_PREFIX/pkgs && \
    chmod -R ugo+w $MAMBA_ROOT_PREFIX

# Install dependencies
COPY requirements_conda.txt .
RUN micromamba install -y -n base --channel conda-forge --file requirements_conda.txt && \
    micromamba install -y -n base --channel conda-forge python lightgbm gunicorn pefile pandas flask && \
    micromamba clean --all --yes

# Copy all EMBER files
COPY ./ember_lib /ember
RUN /opt/mamba/bin/python setup.py install

# Base image for the final stage
FROM python:3.8.19-bullseye

# Set the working directory
WORKDIR /app

# Copy installed packages from Ember stage
COPY --from=ember /opt/mamba /opt/conda

# Ensure the environment is activated and PATH is correctly set
ENV PATH /opt/conda/bin:$PATH

RUN /opt/conda/bin/python -m pip install --upgrade pip && \
    /opt/conda/bin/python -m pip install --no-cache-dir torch

# Copy the application files
COPY . .

EXPOSE 8080

CMD ["/opt/conda/bin/python", "-m", "gunicorn", "-b", "0.0.0.0:8080", "defender.server:app"]
