# Final Year Project - Hansana Wijethunga (MS25916294)

## Project Title
**Forecasting Energy Consumption Using Deep Learning Techniques**

## Student Information
- **Name:** Hansana Chamal Wijethunga  
- **Index Number:** MS25916294  
- **Degree Programme:** MSc in Enterprise Applications Development  
- **Institution:** Sri Lanka Institute of Information Technology  
- **Academic Year:** 2024/2025  

---

## Abstract
The project explores the use of deep learning techniques, particularly LSTM (Long Short-Term Memory) networks, for forecasting energy consumption. It highlights the need for accurate energy prediction models to support energy management and sustainability. The research compares traditional machine learning models with deep learning models, using real-world datasets, and evaluates performance using various metrics.

---

## Table of Contents
1. Introduction  
2. Problem Domain  
3. Aims and Objectives  
4. Methodology  
5. Literature Review  
6. System Architecture  
7. Implementation  
8. Evaluation  
9. Conclusion  
10. References  

---

## 1. Introduction
Energy consumption forecasting is essential for managing energy production, distribution, and consumption. This project implements deep learning models, specifically LSTM networks, to predict energy usage patterns. The study addresses limitations in traditional statistical methods and investigates the effectiveness of deep learning approaches.

---

## 2. Problem Domain
Traditional energy forecasting models often fail to capture nonlinear trends in large datasets. As demand for energy grows, accurate forecasting becomes increasingly critical for energy providers and policy makers. This project focuses on applying advanced deep learning methods to overcome those limitations.

---

## 3. Aims and Objectives

### Aim
To develop an accurate energy consumption forecasting model using deep learning techniques.

### Objectives
- Collect and preprocess historical energy consumption data.
- Explore and evaluate different deep learning models.
- Compare results with traditional forecasting methods.
- Deploy the model for real-time predictions.
- Provide visual representations of predictions.

---

## 4. Methodology
- **Data Collection:** Obtained from UK National Grid via Kaggle.
- **Data Preprocessing:** Includes handling missing values, feature scaling, and time-series transformation.
- **Modeling:** LSTM model implemented using Python and TensorFlow.
- **Evaluation:** Metrics such as MAE, RMSE, and R² used to assess model accuracy.

---

## 5. Literature Review
Several forecasting models were studied including:
- **ARIMA:** Effective for linear time-series forecasting.
- **Random Forest and SVR:** Improved over statistical models but lack in temporal dependency modeling.
- **Deep Learning (LSTM):** Superior in handling sequential and non-linear data.

Findings from multiple sources supported the effectiveness of LSTM for energy prediction tasks.

---

## 6. System Architecture
The system consists of:
- Data ingestion and preprocessing layer
- Deep learning prediction engine
- Evaluation and visualization module
The architecture supports modularity and scalability for future enhancements.

---

## 7. Implementation
- **Tools Used:** Python, TensorFlow, Pandas, Matplotlib, Scikit-learn
- **Model Used:** LSTM with multiple hidden layers and dropout regularization.
- **Training:** Data split into training and test sets with normalization.
- **Deployment:** Model tested with unseen data and visualized using graphs.

---

## 8. Evaluation
Model performance measured using:
- **Mean Absolute Error (MAE)**
- **Root Mean Squared Error (RMSE)**
- **R² Score**

Results showed that the LSTM model significantly outperformed baseline models like ARIMA and SVR.

---

## 9. Conclusion
Deep learning techniques, especially LSTM, are effective in forecasting energy consumption. This project demonstrated the model's superior performance in capturing complex patterns, contributing towards efficient energy management. Future work could include integrating external factors like weather data for better accuracy.

---

## 10. References
1. Box, G. E. P., Jenkins, G. M., & Reinsel, G. C. (2015). *Time Series Analysis: Forecasting and Control*.
2. Hochreiter, S., & Schmidhuber, J. (1997). Long short-term memory. *Neural computation*, 9(8), 1735-1780.
3. Brownlee, J. (2017). *Deep Learning for Time Series Forecasting: Predict the Future with MLPs, CNNs and LSTMs in Python*.
4. Kaggle Dataset: https://www.kaggle.com/datasets/nicholasjhana/energy-consumption-generation-prices-and-weather

---

