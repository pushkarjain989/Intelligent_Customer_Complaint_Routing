import os
os.environ["USE_TF"] = "0"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer

m = SentenceTransformer('all-MiniLM-L6-v2')
df = pd.read_csv('archive (3)/Tweets.csv').dropna(subset=['text']).head(1500)
embs = m.encode(df['text'].tolist(), normalize_embeddings=True)

query = "@AmericanAir Flight UA458 from Chicago is delayed by 45 minutes. Can you provide updated departure time and gate number?"
q = m.encode([query], normalize_embeddings=True)[0]

sims = np.dot(embs, q)
top5 = np.argsort(sims)[::-1][:5]
print("Query:", query)
for i in top5:
    print(f"  {sims[i]:.4f}: {df.iloc[i]['text']}")
