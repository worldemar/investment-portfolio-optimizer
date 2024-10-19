from modules.Portfolio import Portfolio


class UserPortfolio(Portfolio):
    def __init__(self, asset_allocation: dict[str, int]):
        super().__init__(assets=list(asset_allocation.keys()), weights=list(asset_allocation.values()), plot_always=True, plot_marker='X')