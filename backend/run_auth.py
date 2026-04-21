from app import create_app

app = create_app(service_name='auth')

if __name__ == '__main__':
    print(" Auth Service starting on port 5001...")
    app.run(port=5001, debug=False)
