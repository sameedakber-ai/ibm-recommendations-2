import numpy as np
import pandas as pd
from sqlalchemy import create_engine

# Read data
df = pd.read_csv('data/user-item-interactions.csv')
df_content = pd.read_csv('data/articles.csv')
del df['Unnamed: 0']
del df_content['Unnamed: 0']

# <----- Clean data [start] ----->
# Remove duplicate articles
df_content.drop_duplicates(inplace=True, keep='first')
df_content.drop_duplicates(subset='article_id', inplace=True, keep='first')

# Format matching columns to same type
df = df.astype({'article_id': int}).astype({'article_id': str})
df_content = df_content.astype({'article_id': str})

# Make User-id column in df to identify users
user_id_dict = dict()
i=0
for email in df.email:
	if email not in user_id_dict:
		user_id_dict[email] = i
		i+=1
df['user_id'] = df.email.apply(lambda x: user_id_dict[x])
df.drop('email', axis=1, inplace=True)
# <----- Clean data [finished] ----->

# Merge data-sets on article id
df_merged = df.drop('title', axis=1).merge(df_content[['article_id', 'doc_full_name', 'doc_description']], on='article_id', how='inner')

# Save data to database
engine = create_engine('sqlite:///data/data.db')
df_merged.to_sql('categories', engine, index=False, if_exists='replace')