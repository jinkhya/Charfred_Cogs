import logging
import secrets
from collections import namedtuple

log = logging.getLogger('charfred')

Enjinsession = namedtuple('Enjinsession', 'session_id user_id username')


async def post(clientsession, payload, url):
    requestid = secrets.randbelow(60000)
    payload['jsonrpc'] = '2.0'
    payload['id'] = requestid
    async with clientsession.post(f'{url}/api/v1/api.php',
                                  json=payload) as r:
        if r.status == 200:
            content = await r.json()
            if int(content['id']) != requestid:
                log.warning('Request ID and response ID do not match! Abort!')
                return None
            return content
        else:
            return None


async def login(clientsession, enjinlogin):
    if enjinlogin:
        payload = {
            'method': 'User.login',
            'params': {
                'email': enjinlogin.email,
                'password': enjinlogin.password
            }
        }
        resp = await post(clientsession, payload, enjinlogin.url)
        if resp:
            try:
                result = resp['result']
                enjinsession = Enjinsession(
                    session_id=result['session_id'],
                    user_id=result['user_id'],
                    username=result['username']
                )
            except KeyError:
                log.error('Enjin login failed, response content malformed!')
            else:
                log.info('Enjin login successful!')
                return enjinsession
        else:
            log.warning('Enjin login failed!')
        return None


async def verifysession(clientsession, enjinlogin):
    if enjinlogin:
        payload = {
            'method': 'User.checkSession',
            'params': {
                'session_id': enjinlogin.session_id
            }
        }
        resp = await post(clientsession, payload, enjinlogin.url)
        if resp:
            try:
                valid = resp['result']['hasIdentity']
            except KeyError:
                log.error('Enjin session verification failed, response content malformed!')
            else:
                if valid:
                    log.info('Enjin session valid!')
                    return True
                else:
                    log.info('Enjin session invalid!')
                    return False
        else:
            log.warning('Enjin session verification failed!')
        return False
