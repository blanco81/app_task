blacklisted_tokens = set()

def add_token_to_blacklist(token: str):
    blacklisted_tokens.add(token)

def is_token_blacklisted(token: str) -> bool:
    return token in blacklisted_tokens

#Nota: En producción es mejor usar Redis con expiración automática (EXPIRE) 
#para que los tokens caduquen y no llenar la memoria.