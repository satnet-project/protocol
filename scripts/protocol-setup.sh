create_testing_keys()
{
    mkdir key
    # 1: Generate a Private Key
    echo '>>> Generating a private key'
    openssl genrsa -des3 -passout pass:satnet -out key/test.key 1024
    # 2: Generate a CSR (Certificate Signing Request)
    echo '>>> Generating a CSR'
    openssl req -new -key key/test.key -passin pass:satnet -out key/test.csr -subj /CN=example.humsat.org/ 
    # 3: Remove Passphrase from Private Key
    echo '>>> Removing passphrase from private key'
    openssl rsa -in key/test.key -passin pass:satnet -out key/test.key
    # 4: Generating a Self-Signed Certificate
    echo '>>> Generating a public key (certificate)'
    openssl x509 -req -days 365 -in key/test.csr -signkey key/test.key -out key/test.crt

    echo '>>> Generating key bundles'
    # 5: Generate server bundle (Certificate + Private key)
    cat key/test.crt key/test.key > key/server.pem
    # 6: Generate clients bundle (Certificate)
    cp key/test.crt key/public.pem    
}

create_testing_keys