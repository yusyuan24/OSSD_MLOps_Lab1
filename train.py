import joblib, mlflow, mlflow.sklearn
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
 
X, y = load_iris(return_X_y=True)
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2)
 
mlflow.set_experiment("iris")
with mlflow.start_run():
    n = 100
    clf = RandomForestClassifier(n_estimators=n).fit(Xtr, ytr)
    mlflow.log_param("n_estimators", n)
    mlflow.log_metric("accuracy", clf.score(Xte, yte))
    mlflow.sklearn.log_model(
    clf,
    "model",
    input_example=Xtr[:5]
    )
    joblib.dump(clf, "model.pkl")
# view runs:  mlflow ui  ->  http://localhost:5000
