
# Product Database Builder

Dynamically build a product database using multiple barcode-driven APIs.

This is a retail-oriented application which is used to dynamically build a product database  on-the-fly.

A Google Sheets document is used in the back-end to store the product entries. This document can then double as a back-end for a Google AppSheet application or even a Google Form to quickly deploy an inventory management solution.

## Usage

Most 'settings' related properties are currently hard-coded within the `product_database_builder.py` script. Pending UPC codes are grabbed from a worksheet within a 'Retail Company' document, and new product entries are written to yet another worksheet.

For example, pending UPC codes can be grabbed from an AppSheet-connected or Forms-connected worksheet with something like this:
```
=filter(  'Front End'!C2:C1000,  not(isnumber(match('Front End'!C2:C1000,  'Product Database'!A:A,  0)))  )
```
This code would be in the "Pending UPCs" sheet. It checks if any UPC from the "Front End" AppSheet-connected worksheet is present in the "Product Database" worksheet. *If not*, list it.

These listed codes are then grabbed by `product_database_builder.py` and sent in GET requests to three APIs. The `get_apis_append_response` function supports any length UPC array. API limits apply. When building a product entry, the `get_apis_append_response` function prioritizes information from certain, 'more accurate', APIs.

...

To actually use the application, run `python ./start.py` in Windows or Linux. Recommended usage is to schedule a cron job to run the application every X minutes.

## Important Notes

This application utilizes `gspread` to interact with the Google Sheets API. This requires creation of a credentials file as outline in https://docs.gspread.org/en/latest/oauth2.html#for-bots-using-service-account.

Utilized APIs are:
* https://www.upcitemdb.com/
* https://barcode.monster/
* https://upcdatabase.org/

#### UPCItemDB 
UPCItemDB has a 100 request per 24 hours limit with a burst limit of 6 requests per minute.

#### UPC Database
UPC Database has a 100 request per 24 hours limit with no / unspecified burst limit.
This API requires an API key. This key is passed in `product_database_builder.py` in the respective API's class constructor and is sanitized to "KEY_HERE".

#### barcode.monster
barcode.monster has no / unspecified request limit with no / unspecified burst limit.
