def es_token_user(request):
    return {'es_token_user': getattr(request, 'es_token_user', False)}
