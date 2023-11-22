import requests
import gspread
from typing import List
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass


def main():
    gclient = gspread.service_account()

    retail_company_document = gclient.open_by_key("KEY_HERE")
    pending_sheet = retail_company_document.worksheet("Pending UPCs")
    database_sheet = retail_company_document.worksheet("Product Database")

    pending_rows = pending_sheet.get("A2:A3")

    if not pending_rows or pending_rows == [["#N/A"]]:
        raise Exception(f"No pending UPCs found in {pending_rows}.")

    pending_upcs = [upc for row in pending_rows for upc in row]

    get_apis_append_response(pending_upcs, database_sheet)


def get_apis_append_response(upcs: List[str], worksheet: gspread.worksheet.Worksheet):
    upcDatabaseAPI = UPCDatabaseAPI(api_key="KEY_HERE")
    upcItemDBAPI = UPCItemDBAPI()
    barcodeMonsterAPI = BarcodeMonsterAPI()

    status1, products1 = upcItemDBAPI.identify(upcs)

    responses2 = [upcDatabaseAPI.identify(upc) for upc in upcs]
    statuses2, products2 = map(list, zip(*responses2))

    responses3 = [barcodeMonsterAPI.identify(upc) for upc in upcs]
    statuses3, products3 = map(list, zip(*responses3))

    if any(status == Status.FAILURE for status in [status1] + statuses2 + statuses3):
        raise Exception("Status.FAILURE for at least one API, no products written.")

    rows = []

    for upc in upcs:
        product1 = next((product for product in products1 if product.upc == upc), None)
        product2 = next((product for product in products2 if product.upc == upc), None)
        product3 = next((product for product in products3 if product.upc == upc), None)

        title = product1.title or product3.title or product2.title or "#NOT_FOUND"
        desc = product1.desc or product3.desc or product2.desc or "#NOT_FOUND"
        brand = product1.brand or product3.brand or product2.brand or "#NOT_FOUND"

        title, desc, brand = [string.upper() for string in [title, desc, brand]]

        rows.append([upc, title, desc, brand])

    worksheet.append_rows(rows)


def ean13_to_upca(ean13: str):
    if len(ean13) == 13:
        return ean13[1:]

    raise ValueError("Invalid EAN-13 code")


@dataclass
class Product:
    upc: str
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
        upc_path: str | None,
        ean_path: str | None,
    ):
        self.url = url
        self.title_path = title_path
        self.desc_path = desc_path
        self.brand_path = brand_path
        self.code_path = code_path
        self.upc_path = upc_path
        self.ean_path = ean_path

    @abstractmethod
    def identify(self):
        pass


class Status(Enum):
    SUCCESS = 0
    FAILURE = 1


class UPCItemDBAPI(ProductAPI):
    def __init__(self):
        super().__init__(
            url="https://api.upcitemdb.com/prod/trial/lookup",
            title_path="title",
            desc_path="description",
            brand_path="brand",
            code_path="code",
            upc_path="upc",
            ean_path="ean",
        )

    def identify(self, upcs: List[str]) -> (Status, List[Product]):
        PARAMS = {"upc": ",".join(upcs)}
        response = requests.get(url=self.url, params=PARAMS)
        data = response.json()

        if data[self.code_path] != "OK":
            return (Status.FAILURE, None)

        products = []
        for item in data.get("items", []):
            products.append(
                Product(
                    upc=item.get(self.upc_path, None),
                    title=item.get(self.title_path, None),
                    desc=item.get(self.desc_path, None),
                    brand=item.get(self.brand_path, None),
                )
            )

        returned_upcs = [product.upc for product in products]
        for upc in upcs:
            if upc in returned_upcs:
                continue

            products.append(Product(upc=upc, title=None, desc=None, brand=None))

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
            upc_path=None,
            ean_path="barcode",
        )

    def identify(self, upc: str) -> (Status, Product):
        url = self.url + upc
        headers = {"Authorization": f"Bearer {self.api_key}"}
        response = requests.get(url=url, headers=headers)
        data = response.json()

        match (data.get(self.code_path), data.get("error", {}).get("message")):
            case (False, "Not Found. No product could be found with that code."):
                return (Status.SUCCESS, Product(upc, None, None, None))
            case (False, _):
                return (Status.FAILURE, None)

        return (
            Status.SUCCESS,
            Product(
                upc=upc,
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
            upc_path="code",
            ean_path=None,
        )

    def identify(self, upc: str) -> (Status, Product):
        url = self.url + upc
        response = requests.get(url=url)
        data = response.json()

        code = data.get(self.code_path)
        if code != "active":
            match (code):
                case "not found":
                    return (Status.SUCCESS, Product(upc, None, None, None))
                case _:
                    return (Status.FAILURE, None)

        return (
            Status.SUCCESS,
            Product(
                upc=upc,
                title=data.get(self.title_path, None),
                desc=data.get(self.desc_path, None),
                brand=data.get(self.brand_path, None),
            ),
        )


if __name__ == "__main__":
    main()
