

# Retail Scripts

A few scripts to aid retail processes.

* Google Sheets as back-end, doubles as back-end for AppSheet
* Dynamically build product database from APIs
* Extremely simple very-low-security login system for free AppSheet plan

These scripts are not usable unless a Google Sheets backend with proper layout is established.

## Usage

#### Product Database Builder

You will not be able to use this script without some basic Python knowledge and `gspread` knowledge. Small modifications to `product_database_builder.py` are required.

Most 'settings' related properties are currently hard-coded within the `product_database_builder.py` script. Pending UPC codes are grabbed from a worksheet within a 'Retail Company' document, and new product entries are written to another worksheet within the same document.

For example, pending UPC codes can be grabbed from an AppSheet-connected or Forms-connected worksheet with something like this:
```
=filter(  'Front End'!C2:C1000,  not(isnumber(match('Front End'!C2:C1000,  'Product Database'!A:A,  0)))  )
```
This code would be in the "Pending UPCs" sheet. It checks if any UPC from the "Front End" AppSheet-connected worksheet is present in the "Product Database" worksheet. *If not*, list it.

These listed codes are then grabbed by `product_database_builder.py` and sent in GET requests to three APIs. The `get_apis_append_response` function supports any length UPC array. API limits apply. When building a product entry, the `get_apis_append_response` function prioritizes information from certain, 'more accurate', APIs.

#### Session Token Timeout

Automatically deletes session tokens from a credentials Google Sheet when they are older than 8 hours.

...

To actually use the scripts, run `python ./start.py --script product_database_builder` or `python ./start.py --script session_timeout` in Windows or Linux. Recommended usage is to schedule a 'cron job' to run the desired script every X minutes.

## Important Notes

These scripts utilize `gspread` to interact with the Google Sheets API. This requires creation of a credentials file as outlined in https://docs.gspread.org/en/latest/oauth2.html#for-bots-using-service-account.

Utilized APIs are:
* https://www.upcitemdb.com/
* https://barcode.monster/
* https://upcdatabase.org/

#### UPCItemDB 
UPCItemDB has a 100 request per 24 hours limit with a burst limit of 6 requests per minute.

#### UPC Database
UPC Database has a 100 request per 24 hours limit with no / unspecified burst limit.
This API requires an API key. This key is passed in `product_database_builder.py` in the respective API's class constructor. It is sanitized in the code to "KEY_HERE".

#### barcode.monster
barcode.monster has no / unspecified request limit with no / unspecified burst limit.
