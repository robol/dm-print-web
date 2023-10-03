from flask_basicauth import BasicAuth

from ldap3 import Server, Connection, SAFE_SYNC


class Authentication(BasicAuth):

    def __init__(self, app = None):
        super().__init__(app)

    def check_ldap_credentials(self, base, username, password):
        cn = 'uid=%s,%s' % (username, base)
        server = Server('idmauth.unipi.it')
        conn = Connection(server, cn, password, client_strategy = SAFE_SYNC)
        conn.start_tls()
        status, result, response, _ = conn.search(cn, '(objectclass=*)')
        return status

    def check_credentials(self, username, password):        
        return self.check_ldap_credentials('dc=dm,ou=people,dc=unipi,dc=it', username, password)