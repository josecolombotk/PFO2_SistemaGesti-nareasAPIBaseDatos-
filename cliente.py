import json
import urllib.request
from http.cookiejar import CookieJar

BASE_URL = "http://127.0.0.1:5000"

class Cliente:
    def __init__(self):
        self.cookies = CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookies)
        )

    def post(self, path, data):
        req = urllib.request.Request(
            BASE_URL + path,
            data=json.dumps(data).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        return self._send(req)

    def get(self, path):
        req = urllib.request.Request(BASE_URL + path)
        return self._send(req)

    def _send(self, req):
        try:
            with self.opener.open(req) as r:
                return r.getcode(), r.read().decode()
        except Exception as e:
            return 0, str(e)

def main():
    api = Cliente()

    while True:
        print("\n1) Registro\n2) Login\n3) Ver tareas\n4) Salir")
        op = input("Opción: ")

        if op == "1":
            u = input("Usuario: ")
            p = input("Contraseña: ")
            print(api.post("/registro", {"usuario": u, "contraseña": p}))

        elif op == "2":
            u = input("Usuario: ")
            p = input("Contraseña: ")
            print(api.post("/login", {"usuario": u, "contraseña": p}))

        elif op == "3":
            print(api.get("/tareas"))

        elif op == "4":
            break

if __name__ == "__main__":
    main()