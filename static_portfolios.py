from modules.portfolio import Portfolio

STATIC_PORTFOLIOS = [
    Portfolio(plot_always=True, plot_marker='X', weights={
        'Акции РФ': 60,
        'Серебро': 20,
        'Золото': 20,
    }),
    Portfolio(plot_always=True, plot_marker='X', weights={
        'Акции РФ': 60,
        'Золото': 40,
    }),
    Portfolio(plot_always=True, plot_marker='X', weights={
        'Акции РФ': 33.334,
        'Золото': 33.333,
        'Гос. облигации РФ (до 3 лет)': 33.333,
    }),
    Portfolio(plot_always=True, plot_marker='X', weights={
        'Акции РФ': 33.334,
        'Золото': 33.333,
        'Гос. облигации РФ (ОФЗ-ИН)': 33.333,
    }),
    Portfolio(plot_always=True, plot_marker='X', weights={
        'Жильё в РФ': 33.334,
        'Гос. облигации РФ (до 3 лет)': 33.333,
        'Гос. облигации РФ (ОФЗ-ИН)': 33.333,
    }),
    Portfolio(plot_always=True, plot_marker='X', weights={
        'Жильё в РФ': 25,
        'Акции РФ': 25,
        'Золото': 25,
        'Гос. облигации РФ (до 3 лет)': 25,
    }),
    Portfolio(plot_always=True, plot_marker='X', weights={
        'Жильё в РФ': 25,
        'Акции РФ': 25,
        'Золото': 12.5,
        'Серебро': 12.5,
        'Гос. облигации РФ (до 3 лет)': 12.5,
        'Гос. облигации РФ (ОФЗ-ИН)': 12.5,
    }),
]
