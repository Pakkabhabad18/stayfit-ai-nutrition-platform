# StayFit - Progressive Web App (PWA) & Mobile Testing Guide

This guide explains how to use the StayFit Progressive Web App (PWA) features and how to test the application on a mobile device within your local network.

## ✨ PWA Features
StayFit has been enhanced with PWA capabilities to provide a native-like experience on mobile and desktop:
- **Installable**: Add StayFit to your home screen or app drawer.
- **Standalone Mode**: Runs without the browser address bar or navigation buttons.
- **Offline Readiness**: Basic assets and UI are cached via Service Workers.
- **Mobile Navigation**: A specialized bottom navigation bar is implemented for small screens.

---

## 📱 Local Network Testing (Android/iOS)

To run StayFit on your phone and talk to your Mac's backend, follow these steps:

### 1. Network Setup
- Connect your Mac and your mobile device to the **same Wi-Fi network**.
- Find your Mac's Local IP address by running:
  ```bash
  ipconfig getifaddr en0
  ```
  *(Example IP: `192.168.1.50`)*

### 2. Configuration Changes Implemented
The following architectural changes have been made to allow cross-device communication:

#### Backend (Binding to all interfaces)
All backend entry points are configured to use `host='0.0.0.0'` instead of `127.0.0.1`. This allows the server to accept connections from other devices on your network.
- **Files affected**: `api_gateway.py`, `run_auth.py`, `run_meals.py`, `run_analytics.py`, `run_notifications.py`, `run_monolith.py`.

#### Frontend (Network-Aware URLs)
The frontend is configured to point to your Mac's specific IP address so your phone knows where to find the API.
- **API Base**: Updated in `frontend/src/services/api.js`.
- **Notifications**: SSE stream URL updated in `frontend/src/components/Layout.jsx`.
- **Images**: Meal photo source URLs updated in `Dashboard.jsx` and `MealLogger.jsx`.

### 3. How to Run
1. **Start the Backend**:
   ```bash
   cd backend
   python start_microservices.py
   ```
2. **Start the Frontend with Host Flag**:
   ```bash
   cd frontend
   npm run dev -- --host
   ```

### 4. Installing on Android
1. Open **Chrome** on your Android device.
2. Navigate to your Mac's IP on port 5173 (e.g., `http://192.168.1.50:5173`).
3. **Crucial Security Step (for HTTP)**:
   - Since the app is running on `http` (not `https`), Chrome blocks PWA installation by default.
   - On your phone's Chrome, go to: `chrome://flags/#unsafely-treat-insecure-origin-as-secure`
   - Paste your Mac's URL: `http://192.168.1.50:5173`
   - Select **Enabled** and Relaunch Chrome.
4. **Install**: Tap the **three dots (⋮)** in Chrome and select **"Install app"** or **"Add to Home screen"**.

---

## 🛠️ Summary of Changed Files

| Component | File Path | Change Description |
|-----------|-----------|--------------------|
| **Backend** | `api_gateway.py` | Added `host='0.0.0.0'` to `app.run()` |
| **Backend** | `run_auth.py` | Added `host='0.0.0.0'` to `app.run()` |
| **Backend** | `run_meals.py` | Added `host='0.0.0.0'` to `app.run()` |
| **Backend** | `run_analytics.py` | Added `host='0.0.0.0'` to `app.run()` |
| **Backend** | `run_notifications.py` | Added `host='0.0.0.0'` to `app.run()` |
| **Backend** | `run_monolith.py` | Added `host='0.0.0.0'` to `app.run()` |
| **Frontend** | `src/services/api.js` | Replaced `localhost` with Mac IP in `API_BASE` |
| **Frontend** | `src/components/Layout.jsx` | Updated SSE URL and added Mobile Nav Bar |
| **Frontend** | `src/pages/Dashboard.jsx` | Updated image URLs for mobile viewing |
| **Frontend** | `src/pages/MealLogger.jsx` | Updated image URLs for mobile viewing |
| **Frontend** | `src/index.css` | Added styles for Mobile Bottom Navigation |
| **Frontend** | `vite.config.js` | Added `vite-plugin-pwa` configuration |
| **Frontend** | `index.html` | Added PWA meta tags and theme color |
