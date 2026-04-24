from app import create_app

app = create_app(service_name='notifications')

if __name__ == '__main__':
    print(" Notifications Service starting on port 5004...")
    app.run(port=5004, debug=False)
