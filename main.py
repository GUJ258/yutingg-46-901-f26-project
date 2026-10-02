from cmu_cpcs_utils import testFunction
from fc_utils import PQ

################################################################################
# Order
################################################################################

BUY = 'Buy'
SELL = 'Sell'

class Order:
    """An order to buy/sell a currency pair"""

    def __init__(self, base, quote, direction, price, quantity, time):
        """
        Initializes an order

        Args:
            base: The base currency
            quote: The quote currency
            direction: The direction (BUY or SELL)
            price: The price (amount of quote currency) for 1 unit of base currency
            quantity: The amount of the base currency to buy/sell
            time: The time the order was made

        Other Properties:
            fills: A list of (quantity, price) tuples representing amount 
                filled and the price it was filled at. This is a list
                because an order can be filled by multiple different orders
                at different prices, so we need to track all of them.
        """
        self.base = base
        self.quote = quote
        self.direction = direction
        self.price = price
        self.quantity = quantity
        self.time = time

    
    def __repr__(self):
        return (f"Order({self.base}, {self.quote}, {self.direction}, "
                f"{self.price}, {self.quantity}, {self.time})")

################################################################################
# OrderBook
################################################################################

class OrderBook:
    """An order book for one currency pair"""

    def __init__(self):
        """
        Initializes an order book for a single currency pair.
        
        Stores both buy and sell orders that are pending fulfillment for the 
        currency pair. Stored to allow fast matching, prioritizing who is
        fulfilling the order. i.e.
        - Sellers will match with the buyer willing to pay the highest price
        - Buyers will match with sellers who want the lowest price
        - When tied, the earlier order is prioritized

        Properties:
            bids: The BUY orders that have yet to be fulfilled
            asks: The SELL orders that have yet to be fulfilled
        """
        self.bids = PQ(lambda order: (-order.price, order.time))
        self.asks = PQ(lambda order: (order.price, order.time))

    def __repr__(self):
        return f"OrderBook(bids={self.bids}, asks={self.asks})"

    def processOrder(self, order):
        """
        Updates the order book based on the order given.

        If the order can be fulfilled, it is fulfilled starting with the best
        offer currently available. The order given can be fully, partially,
        or not fulfilled. If not completely fulfilled, it is added to orders
        pending fulfillment. 
        
        Any orders filled (completely or partially) will have their quantity
        updated. They will also have a tuple (quantity, price) added to their
        list of fills.

        Args:
            order: The new order to fill.
        """
        # Deal with BUY first， 
        if order.direction == "BUY":
            while order.quantity > 0 and not self.asks.isEmpty():
                best_ask = self.asks.peek()
                # can deal with all/partial best ask
                if best_ask.price <= order.price:
                    best_ask = self.asks.pop()
                    fill_quantity = min(order.quantity, best_ask.quantity)
                    fill_price = best_ask.price

                    order.quantity -= fill_quantity
                    best_ask.quantity -= fill_quantity

                    order.fills.append((fill_quantity, fill_price))
                    best_ask.fills.append((fill_quantity, fill_price))

                    if best_ask.quantity > 0:
                        self.asks.push(best_ask)
                # cant do the best
                else:
                    break
            if order.quantity > 0:
                self.bids.push(order)

        else:
            while order.quantity > 0 and not self.bids.isEmpty():
                best_bid = self.bids.peek()
                # can deal with all/partial best bid
                if best_bid.price >= order.price:
                    best_bid = self.bids.pop()
                    fill_quantity = min(order.quantity, best_bid.quantity)
                    fill_price = best_bid.price

                    order.quantity -= fill_quantity
                    best_bid.quantity -= fill_quantity

                    order.fills.append((fill_quantity, fill_price))
                    best_bid.fills.append((fill_quantity, fill_price))

                    if best_bid.quantity > 0:
                        self.bids.push(best_bid)
                # cant do the best
                else:
                    break
            if order.quantity > 0:
                self.asks.push(order)


################################################################################
# Testing
################################################################################

@testFunction
def testOrderBooks():
    # Test 1: test an orderbook with just one buy bid
    book1 = OrderBook()
    buy1 = Order("EUR", "USD", BUY, price = 100, quantity = 5, time = 1)
    book1.processOrder(buy1)
    assert(not book1.bids.isEmpty())
    assert(book1.asks.isEmpty())
    assert(book1.bids.peek() == buy1)
    assert(buy1.fills == [])

    # Test 2: test an orderbook with just one sell bid
    book2 = OrderBook()
    sell2 = Order("USD", "EUR", SELL, price = 120, quantity = 3, time = 2)
    book2.processOrder(sell2)
    assert(not book2.asks.isEmpty())
    assert(book2.bids.isEmpty())
    assert(book2.asks.peek() == sell2)
    assert(sell2.fills == [])

    # Test 3: check that you fulfill an order if you can
    buy2 = Order("USD", "EUR", BUY, price = 120, quantity = 3, time = 2)
    book2.processOrder(buy2)
    # there should be no additional orders remaining in the book
    # as all of them are fulfilled
    assert(book2.bids.isEmpty() and book2.asks.isEmpty())
    assert(buy2.quantity == 0 and sell2.quantity == 0)

    # Test 4: fill as much of an order as you can (adding a buy second)
    book4 = OrderBook()
    sell4 = Order("USD", "EUR", SELL, price = 90, quantity = 3, time = 1)
    book4.processOrder(sell4)
    buy4 = Order("USD", "EUR", BUY, price = 100, quantity = 5, time = 2)
    book4.processOrder(buy4)
    assert(buy4.quantity == 2)   # still wants 2 more
    assert(sell4.quantity == 0)  # completely filled
    assert(buy4.fills == [(3, 90)])
    assert(book4.bids.peek() == buy4)
    assert(book4.asks.isEmpty())

    # Test 5: fill as much of an order as you can (adding a sell second)
    book5 = OrderBook()
    buy5 = Order("USD", "EUR", BUY, price = 95, quantity = 4, time = 1)
    book5.processOrder(buy5)
    sell5 = Order("USD", "EUR", SELL, price = 90, quantity = 6, time = 2)
    book5.processOrder(sell5)
    assert(sell5.quantity == 2)   # 2 left unfilled
    assert(buy5.quantity == 0)    # completely filled

    assert(buy5.fills == [(4, 95)])
    assert(book5.asks.peek() == sell5)

    # Test 6: the best price should win!
    book6 = OrderBook()
    buy6a = Order("USD", "EUR", BUY, price = 100, quantity = 1, time = 1)
    buy6b = Order("USD", "EUR", BUY, price = 110, quantity = 1, time = 2)
    book6.processOrder(buy6a)
    book6.processOrder(buy6b)
    sell6 = Order("USD", "EUR", SELL, price = 100, quantity = 1, time = 3)
    book6.processOrder(sell6)
    # the 110 bid should match first because it's higher and more advantageous
    assert(buy6b.quantity == 0)
    assert(sell6.quantity == 0)
    assert(buy6b.fills == [(1, 110)])
    assert(buy6a.quantity == 1)  # still waiting
    assert(book6.bids.peek() == buy6a)

    # Test 7: the earlier order at same price wins
    book7 = OrderBook()
    buy7a = Order("USD", "EUR", BUY, price = 100, quantity = 1, time = 1)
    buy7b = Order("USD", "EUR", BUY, price = 100, quantity = 1, time = 2)
    book7.processOrder(buy7a)
    book7.processOrder(buy7b)
    sell7 = Order("USD", "EUR", SELL, price = 100, quantity = 1, time = 3)
    book7.processOrder(sell7)
    assert(buy7a.quantity == 0)
    assert(buy7b.quantity == 1)  # still waiting
    assert(sell7.quantity == 0)
    assert(buy7a.fills == [(1, 100)])

    # Test 8: you can fill an order with multiple other orders
    book8 = OrderBook()
    book8.processOrder(Order("USD", "EUR", SELL, price = 90, quantity = 2, time = 1))
    book8.processOrder(Order("USD", "EUR", SELL, price = 95, quantity = 3, time = 2))
    buy8 = Order("USD", "EUR", BUY, price = 100, quantity = 5, time = 3)
    book8.processOrder(buy8)
    assert(buy8.quantity == 0)
    assert(buy8.fills == [(2, 90), (3, 95)])
    assert(book8.asks.isEmpty())

def main():
    testOrderBooks()

main()