# Part 1 starter tests.
# Run:  python tests/tests-part1.py path/to/main.py

import importlib.util
import os
import sys


def loadModule(path):
    """Imports the Python file at path and returns it as a module. The file's
    folder is added to sys.path so its own imports (e.g. fc_utils) resolve."""
    path = os.path.abspath(path)
    sys.path.insert(0, os.path.dirname(path))
    spec = importlib.util.spec_from_file_location('submission', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def buyOrder(price, quantity, time, base='USD', quote='EUR'):
    return Order(base, quote, BUY, price, quantity, time)


def sellOrder(price, quantity, time, base='USD', quote='EUR'):
    return Order(base, quote, SELL, price, quantity, time)


def drain(pq):
    """Returns every order in the PQ, best first. Empties the PQ, so only call
    this once a test is done with the book."""
    items = []
    while not pq.isEmpty():
        items.append(pq.peek())
        pq.pop()
    return items


def bookWith(*orders):
    """Returns a new OrderBook that has processed the given orders in order."""
    book = OrderBook()
    for order in orders:
        book.processOrder(order)
    return book


def testOrderStoresItsFields():
    print('Testing Order fields...', end='')
    order = Order('USD', 'JPY', SELL, 151.25, 40, 7)
    assert order.base == 'USD'
    assert order.quote == 'JPY'
    assert order.direction == SELL
    assert order.price == 151.25
    assert order.quantity == 40
    assert order.time == 7
    assert order.fills == []
    print('Passed!')


def testBuyRestsOnAnEmptyBook():
    print('Testing a buy rests on an empty book...', end='')
    order = buyOrder(0.85, 10, 0)
    book = bookWith(order)
    assert order.quantity == 10
    assert order.fills == []
    assert book.asks.isEmpty() == True
    assert drain(book.bids) == [order]
    print('Passed!')


def testSellRestsOnAnEmptyBook():
    print('Testing a sell rests on an empty book...', end='')
    order = sellOrder(0.85, 10, 0)
    book = bookWith(order)
    assert order.quantity == 10
    assert order.fills == []
    assert book.bids.isEmpty() == True
    assert drain(book.asks) == [order]
    print('Passed!')


def testExactMatchClearsBothSides():
    print('Testing an exact match...', end='')
    ask = sellOrder(0.85, 5, 0)
    bid = buyOrder(0.85, 5, 1)
    book = bookWith(ask, bid)
    assert ask.quantity == 0 and bid.quantity == 0
    assert ask.fills == [(5, 0.85)]
    assert bid.fills == [(5, 0.85)]
    # both orders are completely filled, so neither is left in the book
    assert book.bids.isEmpty() and book.asks.isEmpty()
    print('Passed!')


def testIncomingSmallerThanResting():
    # the resting order keeps its place with less quantity left; the incoming
    # order is completely filled, so it is not added to the book
    print('Testing a partially filled resting order...', end='')
    ask = sellOrder(1.00, 10, 0)
    bid = buyOrder(1.00, 4, 1)
    book = bookWith(ask, bid)
    assert bid.quantity == 0
    assert bid.fills == [(4, 1.00)]
    assert ask.quantity == 6
    assert ask.fills == [(4, 1.00)]
    assert book.bids.isEmpty()
    assert drain(book.asks) == [ask]
    print('Passed!')


def testIncomingLargerThanResting():
    # what's left of the incoming order is added to the book on its own side
    print('Testing a partially filled incoming order...', end='')
    ask = sellOrder(1.00, 4, 0)
    bid = buyOrder(1.00, 10, 1)
    book = bookWith(ask, bid)
    assert ask.quantity == 0
    assert ask.fills == [(4, 1.00)]
    assert bid.quantity == 6
    assert bid.fills == [(4, 1.00)]
    assert book.asks.isEmpty()
    assert drain(book.bids) == [bid]
    print('Passed!')


def testBuySweepsSeveralPriceLevels():
    # the buy keeps filling until the next ask costs more than it will pay
    print('Testing a buy fills against several asks...', end='')
    ask1 = sellOrder(1.00, 5, 0)
    ask2 = sellOrder(1.05, 4, 1)
    ask3 = sellOrder(1.20, 10, 2)
    bid = buyOrder(1.10, 12, 3)
    book = bookWith(ask1, ask2, ask3, bid)
    assert bid.fills == [(5, 1.00), (4, 1.05)]
    assert bid.quantity == 3
    assert ask1.quantity == 0 and ask2.quantity == 0
    assert ask3.quantity == 10 and ask3.fills == []
    assert drain(book.asks) == [ask3]
    assert drain(book.bids) == [bid]
    print('Passed!')


def testFillsAtTheRestingPrice():
    # a buy willing to pay 1.50 against an ask at 1.00 trades at 1.00
    print("Testing fills use the resting order's price...", end='')
    ask = sellOrder(1.00, 5, 0)
    bid = buyOrder(1.50, 5, 1)
    bookWith(ask, bid)
    assert bid.fills == [(5, 1.00)]
    assert ask.fills == [(5, 1.00)]
    print('Passed!')


def testNoTradeWhenPricesMiss():
    print("Testing orders that don't cross...", end='')
    ask = sellOrder(1.00, 5, 0)
    bid = buyOrder(0.99, 5, 1)
    book = bookWith(ask, bid)
    assert ask.fills == [] and bid.fills == []
    assert ask.quantity == 5 and bid.quantity == 5
    assert drain(book.asks) == [ask]
    assert drain(book.bids) == [bid]
    print('Passed!')


def testBuyTakesTheLowestAskFirst():
    print('Testing buys take the cheapest ask...', end='')
    mid = sellOrder(0.85, 5, 0)
    low = sellOrder(0.75, 5, 1)
    high = sellOrder(0.95, 5, 2)
    book = bookWith(mid, low, high)
    bid = buyOrder(1.00, 5, 3)
    book.processOrder(bid)
    assert bid.fills == [(5, 0.75)]
    assert low.quantity == 0
    assert mid.quantity == 5 and high.quantity == 5
    assert drain(book.asks) == [mid, high]
    print('Passed!')


def testSellTakesTheHighestBidFirst():
    print('Testing sells take the highest bid...', end='')
    mid = buyOrder(0.90, 1, 0)
    high = buyOrder(0.95, 1, 1)
    low = buyOrder(0.85, 1, 2)
    book = bookWith(mid, high, low)
    ask = sellOrder(0.80, 1, 3)
    book.processOrder(ask)
    assert ask.fills == [(1, 0.95)]
    assert high.quantity == 0
    assert drain(book.bids) == [mid, low]
    print('Passed!')


def testSamePriceFirstComeFirstServed():
    # at the same price, the order placed first is filled first
    print('Testing first come, first served at the same price...', end='')
    first = sellOrder(0.85, 5, 0)
    second = sellOrder(0.85, 5, 1)
    book = bookWith(first, second)
    bid = buyOrder(0.85, 7, 2)
    book.processOrder(bid)
    assert bid.fills == [(5, 0.85), (2, 0.85)]
    assert first.quantity == 0
    assert second.quantity == 3
    assert drain(book.asks) == [second]
    print('Passed!')


def testAll():
    testOrderStoresItsFields()
    testBuyRestsOnAnEmptyBook()
    testSellRestsOnAnEmptyBook()
    testExactMatchClearsBothSides()
    testIncomingSmallerThanResting()
    testIncomingLargerThanResting()
    testBuySweepsSeveralPriceLevels()
    testFillsAtTheRestingPrice()
    testNoTradeWhenPricesMiss()
    testBuyTakesTheLowestAskFirst()
    testSellTakesTheHighestBidFirst()
    testSamePriceFirstComeFirstServed()
    print('All Part 1 starter tests passed!')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python tests/tests-part1.py path/to/main.py')
        sys.exit(1)
    submission = loadModule(sys.argv[1])
    Order, OrderBook = submission.Order, submission.OrderBook
    BUY, SELL = submission.BUY, submission.SELL
    testAll()
