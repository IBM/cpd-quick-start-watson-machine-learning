# Save Model Using Pickle
import os, pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
import pickle


df_container_data = pd.read_csv(os.path.join('../data', 'data.csv'))
feature_cols = ['temperature', 'cumulative_power_consumption', 'humidity']

# use the list to select a subset of the original DataFrame
X = df_container_data[feature_cols]

# instantiate
linreg = LinearRegression()


# select a Series from the DataFrame
y = df_container_data['maintainence_required']
X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=1)

# fit the model to the training data (learn the coefficients)
linreg.fit(X_train, y_train)

# serializing our model to a file called model.pkl
pickle.dump(linreg, open(os.path.join('../model', "model.pkl"), "wb"))
