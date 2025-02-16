import numpy as np
import pandas as pd

def calculate_max_pain(options_chain):
    """
    Calculate the max pain point for a stock's option chain.
    
    Parameters:
    options_chain (dict): Dictionary containing:
        - 'strike_prices': list of strike prices
        - 'call_oi': list of call option open interest
        - 'put_oi': list of put option open interest
    
    Returns:
    float: The max pain price point
    dict: Total dollar value of pain at each strike price
    """
    strikes = np.array(options_chain['strike_prices'])
    call_oi = np.array(options_chain['call_oi'])
    put_oi = np.array(options_chain['put_oi'])
    
    pain_values = {}
    
    # Calculate pain for each potential stock price (strike price)
    for stock_price in strikes:
        total_pain = 0
        
        # Calculate call option pain
        for idx, strike in enumerate(strikes):
            if stock_price > strike:
                # For calls, loss = (stock price - strike) * open interest
                call_pain = (stock_price - strike) * call_oi[idx]
                total_pain += call_pain
                
        # Calculate put option pain
        for idx, strike in enumerate(strikes):
            if stock_price < strike:
                # For puts, loss = (strike - stock price) * open interest
                put_pain = (strike - stock_price) * put_oi[idx]
                total_pain += put_pain
                
        pain_values[stock_price] = total_pain
    
    # Find the stock price with minimum total pain
    max_pain_price = min(pain_values.items(), key=lambda x: x[1])[0]
    
    return max_pain_price, pain_values

# Example usage
example_data = {
    'strike_prices': [95, 100, 105, 110, 115],
    'call_oi': [500, 700, 400, 300, 200],
    'put_oi': [200, 400, 600, 400, 300]
}

max_pain, pain_distribution = calculate_max_pain(example_data)

print(max_pain)
print(pain_distribution)