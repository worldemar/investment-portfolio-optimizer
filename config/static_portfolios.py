from modules.portfolio import Portfolio

STATIC_PORTFOLIOS = [
    Portfolio.static_portfolio({
        'Акции РФ': 60,
        'Серебро': 20,
        'Золото': 20,
    }),
    Portfolio.static_portfolio({
        'Акции РФ': 60,
        'Золото': 40,
    }),
    Portfolio.static_portfolio({
        'Серебро': 50,
        'Золото': 50,
    }),
    Portfolio.static_portfolio({
        'Акции РФ': 34,
        'ОПИФ российских облигаций': 33,
        'Золото': 33,
    }),
    Portfolio.static_portfolio({
        'Акции РФ': 34,
        'ОПИФ российских облигаций': 34,
        'Золото': 16,
        'Серебро': 16,
    }),
]
