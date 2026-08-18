FROM nginx:1.27.3-alpine@sha256:814a8e88df978ade80e584cc5b333144b9372a8e3c98872d07137dbf3b44d0e4

COPY nginx.conf /etc/nginx/nginx.conf
COPY index.html app.js styles.css /usr/share/nginx/html/

RUN mkdir -p /var/cache/nginx/client_temp \
    /var/cache/nginx/proxy_temp \
    /var/cache/nginx/fastcgi_temp \
    /var/cache/nginx/uwsgi_temp \
    /var/cache/nginx/scgi_temp /var/run/nginx && \
  chown -R nginx:nginx /var/cache/nginx /var/run/nginx

USER nginx
EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
