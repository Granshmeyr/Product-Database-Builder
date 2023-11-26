import requests
import gspread
from typing import List
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass


def main():
    gclient = gspread.service_account()

    retail_company_document = gclient.open_by_key("KEY_HERE")
    pending_sheet = retail_company_document.worksheet("Pending Barcodes")
    database_sheet = retail_company_document.worksheet("Product Database")

    pending_rows = pending_sheet.get("A2:A3")

    if not pending_rows or pending_rows == [["#N/A"]]:
        raise Exception(f"No pending barcodes found in {pending_rows}.")

    pending_barcodes = [barcode for row in pending_rows for barcode in row]

    get_apis_append_response(pending_barcodes, database_sheet)


def get_apis_append_response(
    barcodes: List[str], worksheet: gspread.worksheet.Worksheet
):
    upcDatabaseAPI = UPCDatabaseAPI(api_key="KEY_HERE")
    upcItemDBAPI = UPCItemDBAPI()
    barcodeMonsterAPI = BarcodeMonsterAPI()

    status1, products1 = upcItemDBAPI.identify(barcodes)

    responses2 = [upcDatabaseAPI.identify(barcode) for barcode in barcodes]
    statuses2, products2 = map(list, zip(*responses2))

    responses3 = [barcodeMonsterAPI.identify(barcode) for barcode in barcodes]
    statuses3, products3 = map(list, zip(*responses3))

    print(f"status1: {status1}")
    print(f"products1: {products1}")
    print(f"statuses2: {statuses2}")
    print(f"products2: {products2}")
    print(f"statuses3: {statuses3}")
    print(f"products3: {products3}")

    if any(status == Status.FAILURE for status in [status1] + statuses2 + statuses3):
        raise Exception("Status.FAILURE for at least one API, no products written.")

    rows = []

    for barcode in barcodes:
        product1 = next(
            (product for product in products1 if product.barcode == barcode), None
        )
        product2 = next(
            (product for product in products2 if product.barcode == barcode), None
        )
        product3 = next(
            (product for product in products3 if product.barcode == barcode), None
        )

        title = product1.title or product3.title or product2.title or "#NOT_FOUND"
        desc = product1.desc or product3.desc or product2.desc or "#NOT_FOUND"
        brand = product1.brand or product3.brand or product2.brand or "#NOT_FOUND"

        title, desc, brand = [string.upper() for string in [title, desc, brand]]

        rows.append([barcode, title, desc, brand])

    worksheet.append_rows(rows)


def upc_e_to_upc_a(upc_e: str) -> str:
    if upc_e[0] not in ("0", "1"):
        raise ValueError("Invalid number system.")

    i = upc_e[6]
    if i in ("0", "1", "2"):
        strings = [
            upc_e[0 : 2 + 1],
            upc_e[6],
            "0000",
            upc_e[3 : 5 + 1],
            upc_e[7],
        ]
    elif i == "3":
        strings = [
            upc_e[0 : 3 + 1],
            "00000",
            upc_e[4 : 5 + 1],
            upc_e[7],
        ]
    elif i == "4":
        strings = [upc_e[0 : 4 + 1], "00000", upc_e[5], upc_e[7]]
    elif i in ("5", "6", "7", "8", "9"):
        strings = [upc_e[0 : 5 + 1], "0000", upc_e[6], upc_e[7]]
    else:
        raise Exception()

    return "".join(strings)


@dataclass
class Product:
    barcode: str
    title: str | None
    desc: str | None
    brand: str | None


class ProductAPI(ABC):
    def __init__(
        self,
        url: str,
        title_path: str | None,
        desc_path: str | None,
        brand_path: str | None,
        code_path: str | None,
    ):
        self.url = url
        self.title_path = title_path
        self.desc_path = desc_path
        self.brand_path = brand_path
        self.code_path = code_path

    @abstractmethod
    def identify(self):
        pass


class Status(Enum):
    SUCCESS = 0
    FAILURE = 1


# Only supports upc-a and ean-13
class UPCItemDBAPI(ProductAPI):
    def __init__(self):
        self.upc_a_path = "upc"
        self.ean_13_path = "ean"

        super().__init__(
            url="https://api.upcitemdb.com/prod/trial/lookup",
            title_path="title",
            desc_path="description",
            brand_path="brand",
            code_path="code",
        )

    def identify(self, barcodes: List[str]) -> (Status, List[Product]):
        barcodes_filtered = []
        for barcode in barcodes:
            barcode_length = len(barcode)

            if barcode_length == 12 or barcode_length == 13:
                barcodes_filtered.append(barcode)
            elif barcode_length == 6:
                barcodes_filtered.append(upc_e_to_upc_a(barcode))

        if not barcodes_filtered:
            none_products = []

            for barcode in barcodes:
                none_products.append(
                    Product(barcode=barcode, title=None, desc=None, brand=None)
                )

            return (Status.SUCCESS, none_products)

        PARAMS = {"upc": ",".join(barcodes_filtered)}
        response = requests.get(url=self.url, params=PARAMS)
        data = response.json()

        if data[self.code_path] != "OK":
            return (Status.FAILURE, None)

        products = []
        for item in data.get("items", []):
            searched_barcode = None
            for barcode in barcodes_filtered:
                upc_a = item.get(self.upc_a_path, None)
                ean_13 = item.get(self.ean_13_path, None)

                if barcode == upc_a:
                    searched_barcode = upc_a
                    break

                if barcode == ean_13:
                    searched_barcode = ean_13
                    break

            products.append(
                Product(
                    barcode=searched_barcode,
                    title=item.get(self.title_path, None),
                    desc=item.get(self.desc_path, None),
                    brand=item.get(self.brand_path, None),
                )
            )

        returned_barcodes = [product.barcode for product in products]
        for barcode in barcodes:
            if barcode in returned_barcodes:
                continue

            products.append(Product(barcode=barcode, title=None, desc=None, brand=None))

        return (Status.SUCCESS, products)


class UPCDatabaseAPI(ProductAPI):
    def __init__(self, api_key: str):
        self.api_key = api_key

        super().__init__(
            url="https://api.upcdatabase.org/product/",
            title_path="title",
            desc_path="description",
            brand_path="brand",
            code_path="success",
        )

    def identify(self, barcode: str) -> (Status, Product):
        url = self.url + barcode
        headers = {"Authorization": f"Bearer {self.api_key}"}
        response = requests.get(url=url, headers=headers)
        data = response.json()

        match (data.get(self.code_path), data.get("error", {}).get("message")):
            case (False, "Not Found. No product could be found with that code."):
                return (Status.SUCCESS, Product(barcode, None, None, None))
            case (False, _):
                return (Status.FAILURE, None)

        return (
            Status.SUCCESS,
            Product(
                barcode=barcode,
                title=data.get(self.title_path, None),
                desc=data.get(self.desc_path, None),
                brand=data.get(self.brand_path, None),
            ),
        )


class BarcodeMonsterAPI(ProductAPI):
    def __init__(self):
        super().__init__(
            url="https://barcode.monster/api/",
            title_path="description",
            desc_path="description",
            brand_path="company",
            code_path="status",
        )

    def identify(self, barcode: str) -> (Status, Product):
        url = self.url + barcode
        response = requests.get(url=url)
        data = response.json()

        code = data.get(self.code_path)
        if code != "active":
            match (code):
                case "not found":
                    return (Status.SUCCESS, Product(barcode, None, None, None))
                case _:
                    return (Status.FAILURE, None)

        return (
            Status.SUCCESS,
            Product(
                barcode=barcode,
                title=data.get(self.title_path, None),
                desc=data.get(self.desc_path, None),
                brand=data.get(self.brand_path, None),
            ),
        )


if __name__ == "__main__":
    main()
