from flask import json

from testplan.runnable.interactive import http


def main():
    app, api = http.generate_interactive_api(None, None)
    app.config["SERVER_NAME"] = "localhost"
    with app.app_context():
        print(json.dumps(api.__schema__, indent=2))


if __name__ == "__main__":
    main()

