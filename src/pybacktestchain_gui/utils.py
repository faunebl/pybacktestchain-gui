import polars as pl 
import requests


# function to retrieve the tickers dataframe
# 
def get_tickers() -> pl.DataFrame:
    """function to retrieve the tickers dataframe

    Returns:
        pl.DataFrame: a dataframe with all of the nasdaq tickers with a non null market cap and IPO year
        column names : 'symbol', 'name', 'volume', 'marketCap', 'ipoyear', 'country', 'industry', 'sector'
    """    
    headers = {
        'authority': 'api.nasdaq.com',
        'accept': 'application/json, text/plain, */*',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36',
        'origin': 'https://www.nasdaq.com',
        'sec-fetch-site': 'same-site',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'referer': 'https://www.nasdaq.com/',
        'accept-language': 'en-US,en;q=0.9',
    }

    params = (
        ('tableonly', 'true'),
        ('limit', '25'),
        ('offset', '0'),
        ('download', 'true'),
    )

    r = requests.get('https://api.nasdaq.com/api/screener/stocks', headers=headers, params=params)
    data = r.json()['data']

    return (
        pl.DataFrame(data=data['rows'])
        .filter(
            ~pl.col('marketCap').eq(""), 
            ~pl.col('ipoyear').eq("")
        )
        .with_columns(
            pl.col('volume').cast(pl.Int128), 
            pl.col('marketCap').cast(pl.Float64),
            pl.col('ipoyear').cast(pl.Int128)
        )
        .select('symbol', 'name', 'volume', 'marketCap', 'ipoyear', 'country', 'industry', 'sector')
    )