FROM nikolaik/python-nodejs:python3.10-nodejs18
ENV APP=/app
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN echo "deb http://deb.debian.org/debian bookworm contrib non-free" > /etc/apt/sources.list.d/contrib.list

RUN  apt-get update \
  && apt-get install -y \
    build-essential \
    gettext \
    libldap2-dev \
    libpq-dev \
    libreoffice \
    libsasl2-dev \
    nginx \
    openssl \
    python-dev-is-python3 \
    ttf-mscorefonts-installer \
    unixodbc-dev \
    unixodbc \
    vim

# This block loads the drivers required to make pyodbc and microsoft sql server work
# It came from https://docs.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server?view=sql-server-ver16
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
  && curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list \
  && apt-get update \
  && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
  && ACCEPT_EULA=Y apt-get install -y mssql-tools18

# Set the working directory to /app
WORKDIR $APP

# Copy the current directory contents into the container at /app
ADD . $APP

# Setup nginx
COPY nginx.default /etc/nginx/sites-available/default
RUN ln -sf /dev/stdout /var/log/nginx/access.log \
  && ln -sf /dev/stderr /var/log/nginx/error.log

# Build help files
RUN libreoffice --norestore --safe-mode --view --convert-to pdf --outdir $APP/help $APP/help/user_guide.docx \
  && libreoffice --norestore --safe-mode --view --convert-to pdf --outdir $APP/help $APP/help/admin_guide.docx \
  && libreoffice --norestore --safe-mode --view --convert-to pdf --outdir $APP/help $APP/help/high_level_design.docx

# Install the dependencies; build the ui folder; publish frontend
RUN pip install --upgrade pip \
  && pip install -r requirements.txt \
  && cd $APP/ui \
  && npm install \
  && npm run build \
  && cd $APP \
  && python manage.py collectstatic --noinput \
  && chmod a+x /app/start-server.sh

EXPOSE 8020
STOPSIGNAL SIGTERM
CMD ["/app/start-server.sh"]
