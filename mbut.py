import re, json, requests, sys

API_KEY = "97fe7bb2-e6fd-4415-82d5-3412aeb90ff9"
URL = "https://crypto.mashu.lol/api/decrypt"

def decrypt_xdata(xdata: str, xtime: int):
    # bersihkan whitespace + escape sequence \u003d
    clean = re.sub(r"\s+", "", xdata).replace("\\u003d", "=")
    r = requests.post(
        URL,
        headers={
            "Content-Type": "application/json",
            "x-api-key": API_KEY,
        },
        json={"xdata": clean, "xtime": int(xtime)},
        timeout=30,
    )
    if not r.ok:
        print("Status:", r.status_code)
        print("Body:", r.text)
        r.raise_for_status()
    js = r.json()
    return js.get("plaintext", js)

if __name__ == "__main__":
    blob = {"xdata":"ZO_2BVCz4NQTMuR0MXOYuefoSpXkfPNdtRFDAishR5i3FEOeK1GxaDiJT1xU0zBZTuG3U2jmdRtZ\nzC1L1omTT0Jun5U6rASFSy6qkwPe_ur91vCymQyNO3mwOhH3E3tykqjmkblhJODtL2JEtAgKlbYu\nvgQNLe_CXvzuqwogOCGlSbE4smvTEPLn2WwjjqbFRIpIXs7hbVtXn_g7ZOQjCPj05hAyvi0SL0i6\n1t7kCpLRlKm5BbZxWVNPiEuYtwrK1zQhNORvRmVqluxgrGtAX_Qn5wmvkknWsfUEZHO2E2u6Zpi2\nhwidhA41xJ9DD-WpjXMu1AD5RBBpYvU2Ze3l_ctQK2Ux7Yz38eCJltn1zFZrLrNgJOWOcgU8jbKS\nJ8EqIfJ043HjU2XJIJU2oUkRAWDQGRi3m5TbXGimk5KWwZOxYl00mxH80wbYciwwGuVmfQfuvlrv\nnyT0kVyqzjTkMzxrf8loBmFLkp0YG54DKAxHetB3sp0Wx022zCt8ncIByOm5FLyZyXuvDav486J6\ndWdOC2POsxTem9cgn8VezOcoEjQ1C_wCwQCYb8DCNFOu\n","xtime":1756878178519}
    
    result = decrypt_xdata(blob["xdata"], blob["xtime"])
    print(json.dumps(result, indent=2, ensure_ascii=False))
