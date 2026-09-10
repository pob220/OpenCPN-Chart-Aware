FROM debian:trixie
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    autoconf autoconf-archive automake binutils build-essential ca-certificates \
    cmake curl dbus dbus-x11 dpkg-dev file gettext git googletest \
    libarchive-dev libbz2-dev libcxx-serial-dev libcurl4-openssl-dev \
    libdrm-dev libelf-dev libexif-dev libgdk-pixbuf-2.0-dev libglew-dev \
    libgtk-3-dev libjs-highlight.js libjs-mathjax libjsoncpp-dev libltdl-dev \
    liblz4-dev liblzma-dev libpango1.0-dev libshp-dev libsqlite3-dev libssl-dev \
    libtinyxml-dev libtool libudev-dev libusb-1.0-0-dev \
    libwxgtk3.2-dev libwxgtk-webview3.2-dev libwxsvg-dev lsb-release \
    ninja-build nlohmann-json3-dev pkg-config portaudio19-dev \
    python-is-python3 python3-dbus python3-gi python3-tk python3-venv \
    python3-pip python3-build python3-setuptools python3-packaging python3-wheel \
    python3-numpy python3-scipy python3-netcdf4 python3-pyproj python3-xarray \
    rapidjson-dev uuid-dev zlib1g-dev xvfb xauth xdotool \
    libaec-dev libblosc-dev libeccodes-dev libhdf5-dev libnetcdf-dev \
    libproj-dev libqhull-dev libsodium-dev librsvg2-common libzip-dev \
    libzstd-dev patchelf lintian && rm -rf /var/lib/apt/lists/*
RUN useradd --uid 1000 --create-home builder
USER builder
WORKDIR /src
