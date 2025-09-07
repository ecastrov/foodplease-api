from app import create_app

app = create_app()

if __name__ == "__main__":
    # http://127.0.0.1:3000
    app.run(host="0.0.0.0", port=3000, debug=True)