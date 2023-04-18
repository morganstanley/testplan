# to regenerate these certificates use the follwoing commands

#rootCA certificate selfsigned
openssl req -x509 -sha256 -days 1825 -newkey rsa:2048 -keyout rootCA.key -out rootCA.crt -nodes

# server key and csr
openssl req -x509 -sha256 -days 1825 -newkey rsa:2048 -keyout rootCA.key -out rootCA.crt -nodes
# server certificate < set hostname to localhost
openssl x509 -req -CA rootCA.crt -CAkey rootCA.key -in server.csr -out server crt -days 3650 -CAcreateserial


#client key and csr
openssl req -newkey rsa:2048 -nodes -keyout client.key -out client.csr -nodes
# client certificate
openssl x509 -req -CA rootCA.crt -CAkey rootCA.key -in client.csr -out client.crt -days 3650 -CAcreateserial