from app import create_app

app = create_app(service_name='analytics')

if __name__ == '__main__':
    print("Analytics Service starting on port 5003...")
    app.run(port=5003, debug=False)
