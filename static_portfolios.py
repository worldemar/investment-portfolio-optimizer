from modules.portfolio import Portfolio

STATIC_PORTFOLIOS = [
    Portfolio(plot_always=True, plot_marker='X', weights=[
        ('Акции РФ', 60),
        ('Серебро', 20),
        ('Золото', 20)
    ]),
    Portfolio(plot_always=True, plot_marker='X', weights=[
        ('Акции РФ', 60),
        ('Золото', 40),
    ]),
    Portfolio(plot_always=True, plot_marker='X', weights=[
        ('Акции РФ', 33.334),
        ('Золото', 33.333),
        ('Гос. облигации РФ (до 3 лет)', 33.333)
    ]),
]
