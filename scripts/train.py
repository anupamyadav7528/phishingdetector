"""Train one model from a local CSV. Usage: python scripts/train.py --kind url --csv data/urls.csv."""
from pathlib import Path
import argparse, json, sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import joblib, pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, average_precision_score, classification_report, confusion_matrix,
                             f1_score, precision_score, recall_score, roc_auc_score)
from sklearn.model_selection import train_test_split
from phishing_detector.features import html_features, url_features

def main():
    p=argparse.ArgumentParser(); p.add_argument("--kind",choices=["url","text","html"],required=True); p.add_argument("--csv",required=True); p.add_argument("--out",default="artifacts"); a=p.parse_args()
    df=pd.read_csv(a.csv); required={"url":"url","text":"text","html":"html"}[a.kind]
    if required not in df or "label" not in df: raise SystemExit(f"CSV requires columns: {required}, label (0/1)")
    y=df.label.astype(int); values=df[required].fillna("").astype(str)
    if a.kind=="text":
        vectorizer=TfidfVectorizer(ngram_range=(1,2), min_df=1, max_features=20000)
        X=vectorizer.fit_transform(values); feature_names=list(vectorizer.get_feature_names_out())
        model=LogisticRegression(max_iter=1000, class_weight="balanced"); transformer=vectorizer
    else:
        extractor=url_features if a.kind=="url" else html_features
        records=[extractor(v) for v in values]; feature_names=list(records[0]); X=pd.DataFrame(records,columns=feature_names)
        model=RandomForestClassifier(n_estimators=250, random_state=42, class_weight="balanced"); transformer=None
    strat=y if y.nunique()>1 else None
    # Ensure a tiny smoke CSV still leaves at least one example per class in test.
    test_size = max(.25, (y.nunique() / len(y)) if strat is not None else .25)
    Xtr,Xte,ytr,yte=train_test_split(X,y,test_size=test_size,random_state=42,stratify=strat)
    model.fit(Xtr,ytr); probs=model.predict_proba(Xte)[:,1]; pred=(probs>=.5).astype(int)
    metrics={"accuracy":accuracy_score(yte,pred),"precision":precision_score(yte,pred,zero_division=0),"recall":recall_score(yte,pred,zero_division=0),"f1":f1_score(yte,pred,zero_division=0),"confusion_matrix":confusion_matrix(yte,pred).tolist()}
    if yte.nunique()>1: metrics.update({"roc_auc":roc_auc_score(yte,probs),"pr_auc":average_precision_score(yte,probs)})
    out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    joblib.dump((transformer,model) if transformer else model,out/f"{a.kind}_model.joblib")
    (out/f"{a.kind}_metadata.json").write_text(json.dumps({"kind":a.kind,"feature_names":feature_names,"metrics":metrics,"schema":f"{required},label"},indent=2),encoding="utf-8")
    print(json.dumps(metrics,indent=2))
if __name__=="__main__": main()
