# OS, font files, native libraries and Node come from this immutable ARM64 image.
# The 1.65.0 image is not published yet. Install the exact locked 1.65.0 browser
# below; never use the older browser bundled in the dependency image.
FROM mcr.microsoft.com/playwright:v1.64.1-noble@sha256:f609973e8fd93f38a5ddfd706a65805294247dae8d81b2541c0afe2787746197
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
WORKDIR /work/web
COPY package.json package-lock.json ./
RUN npm ci && npx playwright install chromium
COPY quality-environment.json /etc/codeimpact-quality.json
# Do not install/upgrade system packages here: the image digest pins fonts/libs.
