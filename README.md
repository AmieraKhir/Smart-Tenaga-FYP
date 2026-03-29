# Smart Tenaga: AI-Powered Energy Monitoring & Carbon Footprint Alert System

Smart Tenaga is an IoT-based energy monitoring system designed to track real-time electricity usage at extension-level and estimate carbon footprint. The system integrates IoT, machine learning, and cloud analytics to promote energy awareness and sustainable consumption behaviour.

## Overview
This project addresses the issue of unnoticed energy consumption in shared environments such as university accommodations, where electricity usage is often bundled and not individually tracked.

The system provides:
- Real-time energy monitoring
- Carbon footprint estimation (CO₂)
- Short-term energy usage prediction
- High-consumption alert system

## System Architecture
The Smart Tenaga system consists of four main components:

1. **IoT Hardware**
   - ESP32 microcontroller
   - PZEM-004T energy sensor
   - Measures voltage, current, power, and energy

2. **Cloud Platform**
   - ThingSpeak for data storage and visualization

3. **Backend Processing**
   - Python for data cleaning and analysis
   - Machine learning models (Linear Regression, Random Forest)

4. **User Interface**
   - Streamlit dashboard for visualization
   - Telegram bot for alert notifications

## Features
- Real-time monitoring of electrical parameters
- Extension-level energy tracking (multiple devices on one socket)
- Carbon emission estimation using Malaysia grid emission factor
- Predictive analytics for short-term energy usage
- Automated alerts for high energy consumption
- Interactive dashboard for data visualization

## Machine Learning
The system applies a two-stage approach:
- **Regression models** to predict energy usage
- **Classification models** to detect high-consumption events

Models used:
- Linear Regression
- Lasso Regression
- LightGBM
- Random Forest

## Data Source
- Real-time IoT data collected via ESP32 + PZEM-004T
- Data transmitted to ThingSpeak at ~20-second intervals
- Processed into minute-level dataset for analysis

## Note
The IoT hardware setup is no longer functional. Some parts of the coding may be incomplete due to file transfer issues between devices. The uploaded files represent the remaining available code.

## Author
Amiera Jannah Bt. Mohammad Khir  
Bachelor of Computer Science (Hons.)  
Universiti Teknologi PETRONAS

## Project Type
Final Year Project (FYP)
