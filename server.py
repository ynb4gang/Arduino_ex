from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from urllib.request import urlopen
from pathlib import Path
import html

HOST = "0.0.0.0"
PORT = 8180

# IP ESP8266 / Arduino from Serial Monitor
ARDUINO_IP = "172.20.10.10"

BASE_DIR = Path(__file__).resolve().parent
HOME_FILE = BASE_DIR / "home.html"


def clamp_int(value, minimum, maximum):
    value = int(value)
    if value < minimum or value > maximum:
        raise ValueError(f"value {value} is outside {minimum}..{maximum}")
    return value


def send_to_arduino(query):
    action = clamp_int(query.get("action", [""])[0], 0, 2)
    red = clamp_int(query.get("red", ["0"])[0], 0, 255)
    green = clamp_int(query.get("green", ["0"])[0], 0, 255)
    blue = clamp_int(query.get("blue", ["0"])[0], 0, 255)
    delay = clamp_int(query.get("delay", ["10"])[0], 0, 99)
    direction = clamp_int(query.get("dir", ["1"])[0], 1, 2)

    endpoints = {
        0: "fill",
        1: "clear",
        2: "rainbow",
    }

    # Arduino expects:
    # direction(1) + RRGGBB(6) + delay(2) + func(1)
    params = (
        f"{direction}"
        f"{red:02x}{green:02x}{blue:02x}"
        f"{delay:02d}"
        f"{action}"
    )

    endpoint = endpoints[action]
    url = f"http://{ARDUINO_IP}/{endpoint}?params={params}"

    with urlopen(url, timeout=10) as response:
        body = response.read().decode("utf-8", errors="replace")

    return url, body


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/":
            self.send_response(302)
            self.send_header("Location", "/home.html")
            self.end_headers()
            return

        if parsed.path != "/home.html":
            self.send_error(404, "Not found")
            return

        status_html = ""

        try:
            query = parse_qs(parsed.query)

            if "action" in query:
                url, response_body = send_to_arduino(query)

                status_html = (
                    '<div class="ok">'
                    "<b>Command sent</b><br>"
                    f"{html.escape(url)}<br><br>"
                    f"Arduino response: {html.escape(response_body)}"
                    "</div>"
                )

        except Exception as exc:
            status_html = (
                '<div class="error">'
                f"<b>Error:</b> {html.escape(str(exc))}"
                "</div>"
            )

        page = HOME_FILE.read_text(encoding="utf-8")
        page = page.replace("{{STATUS}}", status_html)

        data = page.encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    print(f"Web controller: http://127.0.0.1:{PORT}/home.html")
    print(f"Arduino: http://{ARDUINO_IP}/")
    print("Press Ctrl+C to stop.")

    server = ThreadingHTTPServer((HOST, PORT), Handler)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
    finally:
        server.server_close()
