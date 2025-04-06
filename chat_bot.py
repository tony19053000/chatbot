import pandas as pd
import google.generativeai as genai
import re

# === GEMINI API CONFIG ===
genai.configure(api_key="AIzaSyAZwaGuak0Vzk2pZMjsQFLGw_XWse_r7Go")
model = genai.GenerativeModel('models/gemini-1.5-pro')

# === Load CSV Files ===
stock_df = pd.read_csv('stock_market_data_25y_full.csv')
index_files = {
    'nifty 50': pd.read_csv('NIFTY_50.csv'),
    's&p 500': pd.read_csv('S&P_500.csv'),
    'sensex': pd.read_csv('SENSEX.csv')
}
crypto_df = pd.read_csv('reshaped_crypto_data.csv')


# === Logic Functions ===
def get_stock_prediction(company_name, years):
    filtered = stock_df[stock_df['company_name'].str.lower() == company_name.lower()]
    if filtered.empty:
        return f"No data found for company '{company_name}'."
    num_rows = years * 10
    predicted = filtered.tail(num_rows)[['date', 'company_name', 'open', 'high', 'low', 'close', 'volume']]
    predicted = predicted.rename(columns={"date": "future_date"})
    return predicted.reset_index(drop=True)


def get_index_prediction(index_name, years):
    lowercase_name = index_name.lower()
    if lowercase_name not in index_files:
        return f"No data found for index '{index_name}'."
    df = index_files[lowercase_name]
    num_rows = years * 10
    predicted = df.tail(num_rows)
    predicted = predicted.rename(columns={df.columns[0]: "future_date"})
    return predicted.reset_index(drop=True)


def get_crypto_prediction(coin_name, years):
    lowercase_name = coin_name.lower()
    filtered = crypto_df[crypto_df['coin_name'].str.lower() == lowercase_name]

    # Fuzzy fallback
    if filtered.empty():
        filtered = crypto_df[crypto_df['coin_name'].str.lower().str.contains(lowercase_name)]

    if filtered.empty:
        return f"No data found for coin '{coin_name}'."

    num_rows = years * 10
    predicted = filtered.tail(num_rows)[['timestamp', 'coin_name', 'price', 'volume']]
    predicted = predicted.rename(columns={"timestamp": "future_timestamp"})
    return predicted.reset_index(drop=True)


def get_asset_prediction(name, years):
    if name.lower() in index_files:
        return get_index_prediction(name, years)
    elif name.lower() in stock_df['company_name'].str.lower().values:
        return get_stock_prediction(name, years)
    elif name.lower() in crypto_df['coin_name'].str.lower().values:
        return get_crypto_prediction(name, years)
    else:
        return f"Asset '{name}' not recognized."


def compare_assets(name1, name2, years):
    is_stock_1 = name1.lower() in stock_df['company_name'].str.lower().values
    is_stock_2 = name2.lower() in stock_df['company_name'].str.lower().values

    is_crypto_1 = name1.lower() in crypto_df['coin_name'].str.lower().values
    is_crypto_2 = name2.lower() in crypto_df['coin_name'].str.lower().values

    if is_stock_1 and is_stock_2:
        d1 = get_stock_prediction(name1, years)
        d2 = get_stock_prediction(name2, years)
        return {name1: d1, name2: d2}

    elif is_crypto_1 and is_crypto_2:
        d1 = get_crypto_prediction(name1, years)
        d2 = get_crypto_prediction(name2, years)
        return {name1: d1, name2: d2}

    return f"Cannot compare '{name1}' and '{name2}'. They must both be either companies or cryptocurrencies."


# === Gemini Integration ===
def handle_user_query(query):
    prompt = f"""
You are a finance chatbot. Extract from the user query:
1. If it's a 'predict' or 'compare' task
2. The asset names involved (companies, indexes like 'S&P 500', or coins like 'Bitcoin')
3. The number of years (default to 10 if not mentioned)

User Query: "{query}"

Give output in this format:
Action: predict / compare
Assets: [asset1, asset2 (if compare)]
Years: [number]
"""
    try:
        response = model.generate_content(prompt)
        parsed = response.text.strip()

        action = re.search(r'Action:\s*(\w+)', parsed, re.IGNORECASE)
        assets = re.findall(r'Assets:\s*\[(.*?)\]', parsed, re.IGNORECASE)
        years = re.search(r'Years:\s*\[?(\d+)\]?', parsed, re.IGNORECASE)

        action = action.group(1).lower() if action else "predict"
        assets = [a.strip().strip("'\"") for a in assets[0].split(',')] if assets else []
        years = int(years.group(1)) if years else 10

        if action == "compare" and len(assets) == 2:
            return compare_assets(assets[0], assets[1], years)
        elif action == "predict" and len(assets) == 1:
            return get_asset_prediction(assets[0], years)
        else:
            return "Sorry, I couldn't understand your request clearly."

    except Exception as e:
        return f"Error processing query: {str(e)}"


# === CLI Test ===
if __name__ == "__main__":
    print("💬 Gemini-Powered Financial Chatbot Ready! Type 'exit' to quit.")
    while True:
        query = input("\nAsk your financial query: ")
        if query.strip().lower() == "exit":
            break
        output = handle_user_query(query)
        print(output)
