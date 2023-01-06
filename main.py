import requests
import os
from dotenv import load_dotenv
from web3.logs import DISCARD

from functions.provider import get_provider
from functions.Contracts import getSummon, getHeroRent, getHeroSale, getPowerToken

load_dotenv()
network = "dfk"
w3 = get_provider(network)

contracts = {
    "0xBc36D18662Bb97F9e74B1EAA1B752aA7A44595A7": "HeroSummoning",
    "0xc390fAA4C7f66E4D62E59C231D5beD32Ff77BEf0": "HeroAuction",
    "0x8101CfFBec8E045c3FAdC3877a1D30f97d301209": "HeroRent"
}

api_key = os.environ.get("covalent_key")
headers = {
       'Accept': 'application/json',
}

def getSummoningData(hash):
    #summon_contract = getSummon(w3, network)
    token_contract = getPowerToken(w3, network)
    receipt = w3.eth.get_transaction_receipt(hash)
    transactions = token_contract.events.Transfer().processReceipt(receipt, errors=DISCARD)

    balance = 0
    for transaction in transactions:
        balance += transaction["args"]["value"]/10**18
    return balance

def getSaleData(hash):
    sale_contract = getHeroSale(w3, network)
    receipt = w3.eth.get_transaction_receipt(hash)
    transactions = sale_contract.events.AuctionSuccessful().processReceipt(receipt, errors=DISCARD)

    balance = 0
    for transaction in transactions:
        balance = transaction["args"]["totalPrice"]/10**18 - transaction["args"]["totalPrice"]*0.0375/10**18
    return balance
    
def getBuyData(hash):
    sale_contract = getHeroSale(w3, network)
    receipt = w3.eth.get_transaction_receipt(hash)
    transactions = sale_contract.events.AuctionSuccessful().processReceipt(receipt, errors=DISCARD)
    balance = 0
    for transaction in transactions:
        balance = transaction["args"]["totalPrice"]/10**18
    return balance

def getRentData(hash, address):
    token_contract = getPowerToken(w3, network)
    receipt = w3.eth.get_transaction_receipt(hash)
    transactions = token_contract.events.Transfer().processReceipt(receipt, errors=DISCARD)

    balance = 0
    for transaction in transactions:
        if transaction["args"]["to"] ==  address:
            balance += transaction["args"]["value"]/10**18
    return balance

def get_balance(address):
    balance = 0
    missed_transactions = 0
    url = f"https://api.covalenthq.com/v1/53935/address/{address}/transactions_v2/?key={api_key}&page-size=10000"
    result = requests.get(url, headers=headers)
    if result.status_code != 200: return
    data = result.json()["data"]
    for transaction in data["items"]:
        to_address = w3.toChecksumAddress(transaction["to_address"])
        from_address = w3.toChecksumAddress(transaction["from_address"])
        #print(f"to_address:{to_address}, from_address: {from_address}")
        if to_address in contracts and contracts[to_address] == "HeroSummoning" and from_address == address:
            try:
                balance -= getSummoningData(transaction["tx_hash"])
            except:
                missed_transactions += 1
            
        elif to_address in contracts and contracts[to_address] == "HeroAuction" and from_address != address:
            try:
                balance += getSaleData(transaction["tx_hash"])
            except:
                missed_transactions += 1
        
        elif to_address in contracts and contracts[to_address] == "HeroAuction" and from_address == address:
            try:
                balance -= getBuyData(transaction["tx_hash"])
            except:
                missed_transactions += 1
        
        elif to_address in contracts and contracts[to_address] == "HeroSummoning" and from_address != address:
            try:
                balance += getRentData(transaction["tx_hash"], address)
            except:
                missed_transactions += 1
    return {"balance": balance, "missed_transactions": missed_transactions}

address = "0x7C50D01C7Ba0EDE836bDA6daC88A952f325756e3"
balance_1 = get_balance(address)
print(f"address: {address}, balance: {balance_1['balance']}, missed_transactions: {balance_1['missed_transactions']}")

address = "0xa691623968855b91A066661b0552a7D3764c9a64"
balance_2 = get_balance(address)
print(f"address: {address}, balance: {balance_2['balance']}, missed_transactions: {balance_2['missed_transactions']}")

address = "0xfd768E668A158C173e9549d1632902C2A4363178"
balance_3 = get_balance(address)
print(f"address: {address}, balance: {balance_3['balance']}, missed_transactions: {balance_3['missed_transactions']}")

total_balance = balance_1['balance'] + balance_2['balance'] + balance_3['balance']
print(total_balance)


