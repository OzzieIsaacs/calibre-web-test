import threading
try:
    from cStringIO import StringIO as BytesIO
except ImportError:
    from io import BytesIO

from twisted.internet.protocol import ServerFactory
from twisted.python.components import registerAdapter
from twisted.python import log
from ldaptor.inmemory import fromLDIFFile
from ldaptor.interfaces import IConnectedLDAPEntry
from ldaptor.protocols.ldap import ldaperrors
from ldaptor.protocols.ldap.ldapserver import LDAPServer
from ldaptor.protocols import pureldap
from twisted.internet import defer, ssl
from twisted.internet import reactor
from ldaptor.protocols.ldap import distinguishedname
import time

LDAP_AUTH_ANON = 0
LDAP_AUTH_UNAUTH = 1
LDAP_AUTH_SIMPLE = 2

config1 = b"""\
dn: dc=com
dc: com
objectClass: dcObject

dn: dc=calibreweb,dc=com
dc: calibreweb
objectClass: dcObject
objectClass: organization

dn: ou=people,dc=calibreweb,dc=com
objectClass: organizationalUnit
ou: people

dn: cn=root,dc=calibreweb,dc=com
cn: root
gn: root
mail: admin@calibreweb.com
objectclass: top
objectclass: person
objectClass: inetOrgPerson
sn: admin
userPassword: secret

dn: uid=user0,ou=people,dc=calibreweb,dc=com
objectClass: person
objectClass: organizationalPerson
objectClass: inetOrgPerson
uid: user0
cn: user0
gn: John
sn: Doe
userPassword: terces

dn: uid=user1,ou=people, dc=calibreweb,dc=com
objectClass: person
objectClass: organizationalPerson
objectClass: inetOrgPerson
uid: user1
cn: user1
gn: John
sn: Smith
userPassword: eekretsay

"""

config2 = """\
dn: dc=com
dc: com
objectClass: dcObject

dn: dc=calibreweb,dc=com
dc: calibreweb
objectClass: dcObject
objectClass: organization

dn: ou=people,dc=calibreweb,dc=com
objectClass: organizationalUnit
ou: people

dn: cn=root,dc=calibreweb,dc=com
cn: root
gn: root
mail: admin@calibreweb.com
objectclass: top
objectclass: person
objectClass: inetOrgPerson
sn: admin
userPassword: secret

dn: uid=Mümmy 7,ou=people,dc=calibreweb,dc=com
objectClass: person
objectClass: organizationalPerson
objectClass: inetOrgPerson
uid: Mümmy 7
mail: muemmy@alfa.com
gn: Mu
sn: my
userPassword: terces

dn: uid=执一,ou=people, dc=calibreweb,dc=com
objectClass: person
objectClass: organizationalPerson
objectClass: inetOrgPerson
uid: 执一
mail: onny@beta.org
gn: Chinese
sn: Character
userPassword: eekretsay

#Generic groups
dn: ou=groups,dc=calibreweb,dc=com
objectclass:organizationalunit
ou: groups

# create the cps entry
dn: cn=cps,ou=groups,dc=calibreweb,dc=com
objectclass: groupofnames
cn: cps
member: uid=Mümmy 7,ou=People,dc=calibreweb,dc=com
member: uid=执一,ou=People,dc=calibreweb,dc=com

""".encode('utf-8')

config3 = b"""\
dn: dc=com
dc: com
objectClass: dcObject

dn: dc=calibreweb,dc=com
dc: calibreweb
objectClass: dcObject
objectClass: organization

dn: ou=people,dc=calibreweb,dc=com
objectClass: organizationalUnit
ou: people

dn: cn=root,dc=calibreweb,dc=com
cn: root
gn: root
mail: admin@calibreweb.com
objectclass: top
objectclass: person
objectClass: inetOrgPerson
sn: admin
userPassword: secret

dn: uid=user01,ou=people,dc=calibreweb,dc=com
objectClass: person
objectClass: organizationalPerson
objectClass: inetOrgPerson
mail: user01@gamma.org
mail: user01@beta.com
uid: user01
gn: John
sn: Doe
userPassword: terces

dn: uid=user12,ou=people, dc=calibreweb,dc=com
objectClass: person
objectClass: organizationalPerson
objectClass: inetOrgPerson
uid: user12
gn: John
sn: Smith
userPassword: eekretsay

#Generic groups
dn: ou=groups,dc=calibreweb,dc=com
objectclass:organizationalunit
ou: groups

# create the cps entry
dn: cn=cps,ou=groups,dc=calibreweb,dc=com
objectclass: posixGroup
cn: cps
gidNumber: 5001
memberUid: user01
memberUid: user12

"""

config4 = b"""\
dn: dc=com
dc: com
objectClass: dcObject

dn: dc=calibreweb,dc=com
dc: calibreweb
objectClass: dcObject
objectClass: organization

dn: ou=people,dc=calibreweb,dc=com
objectClass: organizationalUnit
ou: people

dn: cn=root,dc=calibreweb,dc=com
cn: root
gn: root
mail: admin@calibreweb.com
objectclass: top
objectclass: person
objectClass: inetOrgPerson
sn: admin
userPassword: secret

dn: uid=user11,ou=people,dc=calibreweb,dc=com
objectClass: person
objectClass: organizationalPerson
objectClass: inetOrgPerson
mail: user11@gamma.or
mail: user11@beta.com
uid: user11
gn: John1
sn: Doe1
userPassword: terces

dn: uid=user122,ou=people, dc=calibreweb,dc=com
objectClass: person
objectClass: organizationalPerson
objectClass: inetOrgPerson
uid: user122
gn: John1
sn: Smith1
userPassword: eekretsay

#Generic groups
dn: ou=groups,dc=calibreweb,dc=com
objectclass:organizationalunit
ou: groups

# create the cps entry
dn: cn=cps,ou=groups,dc=calibreweb,dc=com
objectclass: groupofnames
cn: cps
member: uid=user122,ou=People,dc=calibreb,dc=com
member: cn=user124,ou=People,dc=calibreweb,dc=com
member: uid=user13,ou=People,dc=calibreweb,dc=com

"""


class Tree(object):

    def __init__(self, config=0):
        global config1, config2, config3
        ldif = None
        if config == 1:
            ldif = config1
        if config == 2:
            ldif = config2
        if config == 3:
            ldif = config3
        if config == 4:
            ldif = config4
        self.f = BytesIO(ldif)
        d = fromLDIFFile(self.f)
        d.addCallback(self.ldifRead)

    def ldifRead(self, result):
        self.f.close()
        self.db = result


class LDAPSTARTTLSServer(LDAPServer):
    """
    An STARTtTLS LDAP server proxy.
    """

    unbound = False
    use_tls = False

    def __init__(self):
        LDAPServer.__init__(self)
        self.startTLS_initiated = False
        self.authentication = LDAP_AUTH_SIMPLE

    def _handle_Bind(self, request, controls, __):
        if request.version != 3:
            raise ldaperrors.LDAPProtocolError(
                'Version %u not supported' % request.version)

        self.checkControls(controls)

        if request.dn == b'' and self.authentication == LDAP_AUTH_ANON:
            # anonymous bind
            self.boundUser = None
            return pureldap.LDAPBindResponse(resultCode=0)
        else:
            dn = distinguishedname.DistinguishedName(request.dn)
            root = IConnectedLDAPEntry(self.factory)
            d = root.lookup(dn)

            def _noEntry(fail):
                fail.trap(ldaperrors.LDAPNoSuchObject)
                return None
            d.addErrback(_noEntry)

            def _gotEntry(entry, auth):
                if entry is None:
                    raise ldaperrors.LDAPInvalidCredentials()
                # hack for unauth request
                if self.authentication == LDAP_AUTH_UNAUTH and auth == b'':
                    self.boundUser = entry
                    msg = pureldap.LDAPBindResponse(
                        resultCode=ldaperrors.Success.resultCode,
                        matchedDN=entry.dn.getText())
                    return msg
                else:
                    d = entry.bind(auth)

                    def _cb(entry):
                        self.boundUser = entry
                        msg = pureldap.LDAPBindResponse(
                            resultCode=ldaperrors.Success.resultCode,
                            matchedDN=entry.dn.getText())
                        return msg
                    d.addCallback(_cb)
                    return d
            d.addCallback(_gotEntry, request.auth)

            return d

    def handle_LDAPBindRequest(self, request, controls, reply):
        if not self.startTLS_initiated and self.use_tls:
            raise ldaperrors.LDAPConfidentialityRequired()
        else:
            return self._handle_Bind(request, controls, reply)
            # return LDAPServer.handle_LDAPBindRequest(self, request, controls, reply)

    def handle_LDAPUnBindRequest(self, request, controls, reply):
        self.startTLS_initiated = False
        return LDAPServer.handle_LDAPUnbindRequest(self, request, controls, reply)

    def handle_LDAPExtendedRequest(self, request, controls, reply):
        """
        Handler for extended LDAP requests (e.g. startTLS).
        """
        if self.debug:
            log.msg("Received extended request: " + request.requestName.decode('utf-8'))
        if request.requestName == pureldap.LDAPStartTLSRequest.oid:
            d = defer.maybeDeferred(self.handleStartTLSRequest, request, controls, reply)
            d.addErrback(log.err)
            return d
        return self.handleUnknown(request, controls, reply)

    def handleStartTLSRequest(self, request, __, reply):
        """
        If the protocol factory has an `options` attribute it is assumed
        to be a `twisted.internet.ssl.CertificateOptions` that can be used
        to initiate TLS on the transport.
        Otherwise, this method returns an `unavailable` result code.
        """

        if self.debug:
            log.msg("Received startTLS request: " + repr(request))
        if hasattr(self.factory, 'options'):
            if self.startTLS_initiated:
                msg = pureldap.LDAPStartTLSResponse(
                    resultCode=ldaperrors.LDAPOperationsError.resultCode)
                log.msg(
                    "Session already using TLS.  "
                    "Responding with 'operationsError' (1): " + repr(msg))
            else:
                if self.debug:
                    log.msg("Setting success result code ...")
                msg = pureldap.LDAPStartTLSResponse(
                    resultCode=ldaperrors.Success.resultCode)
                if self.debug:
                    log.msg("Replying with successful LDAPStartTLSResponse ...")
                reply(msg)
                if self.debug:
                    log.msg("Initiating startTLS on transport ...")
                self.transport.startTLS(self.factory.options)
                self.startTLS_initiated = True
                msg = None
        else:
            msg = pureldap.LDAPStartTLSResponse(
                resultCode=ldaperrors.LDAPUnavailable.resultCode)
            log.msg(
                "StartTLS not implemented.  "
                "Responding with 'unavailable' (52): " + repr(msg))
        return defer.succeed(msg)


class LDAPServerFactory(ServerFactory):
    protocol = LDAPServer

    def __init__(self, root, tls, auth):
        self.root = root
        self.use_TLS = tls
        self.authentication = auth

    def buildProtocol(self, addr):
        proto = LDAPSTARTTLSServer()
        proto.debug = self.debug
        proto.use_tls = self.use_TLS
        proto.authentication = self.authentication
        proto.factory = self
        return proto


class TestLDAPServer(threading.Thread):
    def __init__(self, port=8080, encrypt=None, config=0, auth=LDAP_AUTH_SIMPLE):
        threading.Thread.__init__(self)
        self.is_running = False

        registerAdapter(
            lambda x: x.root,
            LDAPServerFactory,
            IConnectedLDAPEntry)

        self._createListner(port, encrypt, config, auth)

    def _createListner(self, port, encrypt, config, auth):
        tls = False
        cert = None
        tree = Tree(config)
        if encrypt is not None:
            cert = ssl.DefaultOpenSSLContextFactory('./files/ssl.key', './files/ssl.crt')
        if encrypt == 'TLS':
            tls = True
        factory = LDAPServerFactory(tree.db, tls, auth)
        if cert:
            factory.options = cert
        factory.debug = False
        if encrypt == 'SSL':
            self.serv = reactor.listenSSL(port, factory, cert)
        else:
            self.serv = reactor.listenTCP(port, factory)
        # self.serv = reactor.listenSSL(port, factory)
        self.is_running = True

    def stopListen(self):
        if self.is_running:
            def cbloseConnection(result):
                return
                # print('Connection: ' + result)
                # self.is_running = False

            def cberrloseConnection(failure):
                return
                # print('failure Connect: ' + str(failure))
                # self.is_running = False

            # e = self.serv.loseConnection()
            e = defer.maybeDeferred(self.serv.loseConnection)
            e.addCallback(cbloseConnection)
            e.addErrback(cberrloseConnection)
            time.sleep(2)
            '''try:
                self.serv.loseConnection()
            except Exception:
                print('except1')'''
            try:
                self.serv.connectionLost(reason=None)
            except Exception:
                pass

            def cbStopListening(__):
                # print('Stopped: ' + result)
                self.is_running = False

            def cberrStop(failure):
                # print('failure: ' + str(failure))
                self.is_running = False

            d = defer.maybeDeferred(self.serv.stopListening)
            d.addCallback(cbStopListening)
            d.addErrback(cberrStop)
            self.is_running = False
            time.sleep(2)

    def relisten(self, port=8080, encrypt=None, config=0, auth=LDAP_AUTH_SIMPLE):
        self.stopListen()
        self._createListner(port, encrypt, config, auth)

    def is_running(self):
        return self.is_running

    def run(self):
        self.is_running = True
        reactor.run(installSignalHandlers=False)

    def stop_LdapServer(self):
        self.is_running = False
        reactor.callFromThread(reactor.stop)
