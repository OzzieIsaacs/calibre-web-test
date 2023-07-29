import socket
import random
from OpenSSL import crypto
import os

files_path = os.path.dirname(os.path.abspath(__file__))

def _gen_cert_pkey():
    pkey = crypto.PKey()
    pkey.generate_key(crypto.TYPE_RSA, 2048)

    x509 = crypto.X509()
    subject = x509.get_subject()
    subject.commonName = socket.gethostname()
    x509.set_issuer(subject)
    x509.gmtime_adj_notBefore(0)
    x509.gmtime_adj_notAfter(5*365*24*60*60)
    x509.set_pubkey(pkey)
    x509.set_serial_number(random.randrange(100000))
    x509.set_version(2)
    x509.add_extensions([
        crypto.X509Extension(b'subjectAltName', False,
            ','.join([
                'DNS:%s' % socket.gethostname(),
                'DNS:*.%s' % socket.gethostname(),
                'DNS:localhost',
                'DNS:*.localhost']).encode()),
        crypto.X509Extension(b"basicConstraints", True, b"CA:false")])

    x509.sign(pkey, 'SHA256')

    with open('ssl.crt','wb') as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, x509))
    with open('ssl.key','wb') as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, pkey))

def _generate_CA():
    # ssl private key
    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, 4096)

    # Create Certificate Authority Certificate
    ca = crypto.X509()
    ca.set_version(2)
    ca.set_serial_number(1)
    ca.get_subject().CN = socket.gethostname() + " CA"
    ca.gmtime_adj_notBefore(0)
    ca.gmtime_adj_notAfter(365*24 * 60 * 60)
    ca.set_issuer(ca.get_subject())
    ca.set_pubkey(key)
    ca.add_extensions([
        crypto.X509Extension(b"basicConstraints", True,
                             b"CA:TRUE"),
        crypto.X509Extension(b"subjectKeyIdentifier", False, b"hash",
                             subject=ca),
    ])
    ca.sign(key, "sha1")
    with open(os.path.join(files_path, 'files', 'ca.cert.pem'),'wb') as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, ca))

    with open(os.path.join(files_path, 'files', 'ca.cert.key'),'wb') as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key))


def _generate_certificate_signing_request(filename):
    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, 4096)

    req = crypto.X509Req()
    req.get_subject().CN = socket.gethostname()
    req.set_pubkey(key)
    req.sign(key, "sha256")

    # Write server private key
    with open(os.path.join(files_path, 'files', filename + '.key'),'wb') as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key))

    # Write request for signing
    with open(os.path.join(files_path, files_path, 'files', filename + '.csr'),'wb') as f:
        f.write(crypto.dump_certificate_request(crypto.FILETYPE_PEM, req))


def _generate_certificate_from_signing_request(filename):
    ca_cert = crypto.load_certificate(crypto.FILETYPE_PEM,
                                      open(os.path.join(files_path, 'files', 'ca.cert.pem')).read())
    ca_key = crypto.load_privatekey(crypto.FILETYPE_PEM,
                                    open(os.path.join(files_path, 'files', 'ca.cert.key')).read())
    req = crypto.load_certificate_request(crypto.FILETYPE_PEM,
                                          open(os.path.join(files_path, 'files', filename + ".csr")).read())

    cert = crypto.X509()
    cert.set_subject(req.get_subject())
    cert.set_issuer(ca_cert.get_subject())
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(5*365*24*60*60)
    cert.set_pubkey(req.get_pubkey())
    cert.set_serial_number(random.randrange(100000))
    cert.set_version(2)
    cert.sign(ca_key, "sha256")

    with open(os.path.join(files_path, 'files', filename + '.crt'),'wb') as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))


def generate_ssl_testing_files():
    for f in ['ca.cert.pem', 'server.key', 'server.crt', 'client.crt', 'client.key']:
        if not os.path.isdir(os.path.join(files_path, 'files')):
            os.mkdir(os.path.join(files_path, 'files'))
        if not os.path.isfile(os.path.join(files_path, 'files', f)):
            _generate_CA()
            # Create server pkey, signing request -> signed certificate
            _generate_certificate_signing_request('server')
            _generate_certificate_from_signing_request('server')
            # Create client pkey, signing request -> signed certificate
            _generate_certificate_signing_request('client')
            _generate_certificate_from_signing_request('client')
            os.unlink(os.path.join(files_path, 'files', 'server.csr'))
            os.unlink(os.path.join(files_path, 'files', 'client.csr'))


# For emailtesting:
# after the files are generated copy ca.cert.pem to /usr/local/share/ca-certificates and rename the ending to crt (ca.cert.crt)
# now run "sudo update-ca-cert" and the certificate is added to the certificate storage