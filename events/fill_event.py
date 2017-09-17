from events.event import Event


class FillEvent(Event):
    """
    Encapsulates the notion of a Filled Order, as returned
    from a brokerage. Stores the quantity of an instrument
    actually filled and at what price. In addition, stores
    the commission of the trade from the brokerage.
    """

    def __init__(self, timeindex, symbol, exchange, quantity,
                 direction, fill_cost, commission=None):
        """
        Initialises the FillEvent object. Sets the symbol, exchange,
        quantity, direction, cost of fill and an optional
        commission.

        Parameters:
        timeindex - The bar-resolution when the order was filled.
        symbol - The instrument which was filled.
        exchange - The exchange where the order was filled.
        quantity - The filled quantity.
        direction - The direction of fill ('BUY' or 'SELL')
        fill_cost - The holdings value in dollars.
        commission - An optional commission.
        """

        self.type = 'FILL'
        self.timeindex = timeindex
        self.symbol = symbol
        self.exchange = exchange
        self.quantity = quantity
        self.direction = direction

        if commission is None:
            self.commission = 0
        else:
            self.commission = commission

        if fill_cost is None:
            self.fill_cost = 0
        else:
            self.fill_cost = fill_cost

    def get_as_string(self):
        return 'Fill: TimeIndex: %s, Symbol: %s, Exchange: %s, Quantity: %f, Direction: %s,  FillCost: %f' % \
               (self.timeindex, self.symbol, self.exchange, self.quantity, self.direction, self.fill_cost)
