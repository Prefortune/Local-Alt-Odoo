# import requests

# def test_create_document_url():
#     url = "https://secure.cardcom.solutions/api/v11/Transactions/GetTransactionInfoById"

#     payload = {
#         "TerminalNumber": 161326,
#         "UserName": "bY4OnAHlIXCfdzuWq3FU",
#         "UserPassword": "9pIOPoLIj4ZtJdhSIRrP",
#         "InternalDealNumber": 223737519
#         }

#     headers = {
#         "Content-Type": "application/json"
#     }

#     response = requests.post(url, json=payload, headers=headers)

#     print("Status Code:", response.status_code)
#     try:
#         print("Response JSON:", response.json())
#     except Exception:
#         print("Raw Response:", response.text)


# if __name__ == "__main__":
#     test_create_document_url()
