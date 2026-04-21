from app import create_app

app = create_app(service_name='meals')

if __name__ == '__main__':
    print("Meals & Reco Service starting on port 5002...")
    app.run(port=5002, debug=False)
