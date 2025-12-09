# Base image
FROM python:3.11-slim

# ============================================
# Layer 1: System Dependencies (Cacheável)
# ============================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    wget \
    tar \
    xz-utils \
    fonts-liberation \
    fonts-noto-color-emoji \
    fontconfig \
    build-essential \
    yasm \
    cmake \
    meson \
    ninja-build \
    nasm \
    libssl-dev \
    libvpx-dev \
    libx264-dev \
    libx265-dev \
    libnuma-dev \
    libmp3lame-dev \
    libopus-dev \
    libvorbis-dev \
    libtheora-dev \
    libspeex-dev \
    libfreetype6-dev \
    libfontconfig1-dev \
    libgnutls28-dev \
    libaom-dev \
    libdav1d-dev \
    librav1e-dev \
    libsvtav1enc-dev \
    libzimg-dev \
    libwebp-dev \
    git \
    pkg-config \
    autoconf \
    automake \
    libtool \
    libfribidi-dev \
    libharfbuzz-dev \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libxcomposite1 \
    libxrandr2 \
    libxdamage1 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libpangoft2-1.0-0 \
    libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

# ============================================
# Layer 2: Build Native Libraries (Cacheável)
# ============================================

# Install SRT from source
RUN git clone https://github.com/Haivision/srt.git && \
    cd srt && \
    mkdir build && cd build && \
    cmake .. && \
    make -j$(nproc) && \
    make install && \
    cd ../.. && rm -rf srt

# Install SVT-AV1 from source
RUN git clone https://gitlab.com/AOMediaCodec/SVT-AV1.git && \
    cd SVT-AV1 && \
    git checkout v0.9.0 && \
    cd Build && \
    cmake .. && \
    make -j$(nproc) && \
    make install && \
    cd ../.. && rm -rf SVT-AV1

# Install libvmaf from source
RUN git clone https://github.com/Netflix/vmaf.git && \
    cd vmaf/libvmaf && \
    meson build --buildtype release && \
    ninja -C build && \
    ninja -C build install && \
    cd ../.. && rm -rf vmaf && \
    ldconfig

# Build and install fdk-aac
RUN git clone https://github.com/mstorsjo/fdk-aac && \
    cd fdk-aac && \
    autoreconf -fiv && \
    ./configure && \
    make -j$(nproc) && \
    make install && \
    cd .. && rm -rf fdk-aac

# Install libunibreak
RUN git clone https://github.com/adah1972/libunibreak.git && \
    cd libunibreak && \
    ./autogen.sh && \
    ./configure && \
    make -j$(nproc) && \
    make install && \
    ldconfig && \
    cd .. && rm -rf libunibreak

# Build and install libass
RUN git clone https://github.com/libass/libass.git && \
    cd libass && \
    autoreconf -i && \
    ./configure --enable-libunibreak || { cat config.log; exit 1; } && \
    mkdir -p /app && echo "Config log located at: /app/config.log" && cp config.log /app/config.log && \
    make -j$(nproc) || { echo "Libass build failed"; exit 1; } && \
    make install && \
    ldconfig && \
    cd .. && rm -rf libass

# Build and install FFmpeg
RUN git clone https://git.ffmpeg.org/ffmpeg.git ffmpeg && \
    cd ffmpeg && \
    git checkout n7.0.2 && \
    PKG_CONFIG_PATH="/usr/lib/x86_64-linux-gnu/pkgconfig:/usr/local/lib/pkgconfig" \
    CFLAGS="-I/usr/include/freetype2" \
    LDFLAGS="-L/usr/lib/x86_64-linux-gnu" \
    ./configure --prefix=/usr/local \
        --enable-gpl \
        --enable-pthreads \
        --enable-neon \
        --enable-libaom \
        --enable-libdav1d \
        --enable-librav1e \
        --enable-libsvtav1 \
        --enable-libvmaf \
        --enable-libzimg \
        --enable-libx264 \
        --enable-libx265 \
        --enable-libvpx \
        --enable-libwebp \
        --enable-libmp3lame \
        --enable-libopus \
        --enable-libvorbis \
        --enable-libtheora \
        --enable-libspeex \
        --enable-libass \
        --enable-libfreetype \
        --enable-libharfbuzz \
        --enable-fontconfig \
        --enable-libsrt \
        --enable-filter=drawtext \
        --extra-cflags="-I/usr/include/freetype2 -I/usr/include/libpng16 -I/usr/include" \
        --extra-ldflags="-L/usr/lib/x86_64-linux-gnu -lfreetype -lfontconfig" \
        --enable-gnutls \
    && make -j$(nproc) && \
    make install && \
    cd .. && rm -rf ffmpeg

# Add /usr/local/bin to PATH
ENV PATH="/usr/local/bin:${PATH}"

# Copy fonts and rebuild font cache
COPY ./fonts /usr/share/fonts/custom
RUN fc-cache -f -v

# ============================================
# Layer 3: Python Dependencies (Cacheável)
# ============================================
WORKDIR /app

# ============================================
# Layer 13: Upgrade pip (Cacheável - raramente muda)
# ============================================
RUN pip install --upgrade pip

# ============================================
# Layer 14: Copy requirements.txt (Muda quando requirements.txt muda)
# ============================================
COPY requirements.txt .

# ============================================
# Layer 15: Install base dependencies (Cacheável - mudam menos)
# ============================================
RUN pip install Flask Werkzeug requests gunicorn APScheduler flask-restx httpx \
    beautifulsoup4 srt numpy google-auth google-auth-oauthlib \
    google-auth-httplib2 google-api-python-client google-api-core \
    google-cloud-storage google-cloud-run psutil boto3 Pillow matplotlib \
    yt-dlp ffmpeg-python

# ============================================
# Layer 16: Install torch (Cacheável - pesado mas cacheável)
# ============================================
RUN pip install torch

# ============================================
# Layer 17: Install whisper (Cacheável - pesado mas cacheável)
# ============================================
RUN pip install openai-whisper

# ============================================
# Layer 18: Additional Python Packages (Cacheável)
# ============================================
RUN pip install jsonschema

# ============================================
# Layer 19: Setup User and Directories (Cacheável)
# ============================================
RUN useradd -m appuser && \
    mkdir -p /app/whisper_cache && \
    chown -R appuser:appuser /app

ENV WHISPER_CACHE_DIR="/app/whisper_cache"
ENV PYTHONUNBUFFERED=1

# ============================================
# Layer 20: Whisper Model Download (Cacheável)
# ============================================
USER appuser
RUN python -c "import os; print(os.environ.get('WHISPER_CACHE_DIR')); import whisper; whisper.load_model('base')"

# ============================================
# Layer 21: Playwright Installation (Cacheável)
# ============================================
RUN pip install --user playwright && \
    python -m playwright install chromium

# ============================================
# Layer 22: Application Code (Muda Frequentemente)
# ============================================
COPY --chown=appuser:appuser . .

# ============================================
# Layer 23: Final Setup
# ============================================
RUN echo '#!/bin/bash\n\
gunicorn --bind 0.0.0.0:8080 \
    --workers ${GUNICORN_WORKERS:-2} \
    --timeout ${GUNICORN_TIMEOUT:-300} \
    --worker-class sync \
    --keep-alive 80 \
    --config gunicorn.conf.py \
    app:app' > /app/run_gunicorn.sh && \
    chmod +x /app/run_gunicorn.sh

EXPOSE 8080

CMD ["/app/run_gunicorn.sh"]
