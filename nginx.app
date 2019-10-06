location /wss/ {
  if ($http_user_agent !~* "xxx-Client") {
    return 500;
  }

  proxy_redirect off;
  proxy_pass http://127.0.0.1:1234;
  proxy_http_version 1.1;
  proxy_set_header Upgrade $http_upgrade;
  proxy_set_header Connection "upgrade";
  proxy_set_header Host $http_host;
}