def apply_discount(price, rate):
    """price에서 rate(0~1) 비율만큼 할인한 금액을 반환한다."""
    return price - (price * rate)
