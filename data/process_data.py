import numpy as np
import pandas as pd
pd.options.mode.chained_assignment = None
from sqlalchemy import create_engine
from googlesearch import search
from tqdm import tqdm
tqdm.pandas()

# Read data
df = pd.read_csv('data/user-item-interactions.csv')
df_content = pd.read_csv('data/articles.csv')
del df['Unnamed: 0']
del df_content['Unnamed: 0']

# <----- CLEAN DATA [start] ----->
# Remove duplicate articles
df_content.drop_duplicates(inplace=True, keep='first')
df_content.drop_duplicates(subset='article_id', inplace=True, keep='first')

# Format matching columns to same type
df = df.astype({'article_id': int})

# Make User-id column in df to identify users
user_id_dict = dict()
i=0
for email in df.email:
	if email not in user_id_dict:
		user_id_dict[email] = i
		i+=1
df['user_id'] = df.email.apply(lambda x: user_id_dict[x])
df.drop('email', axis=1, inplace=True)

# Fill in missing document descriptions with empty strings
df_content.doc_description[df_content.doc_description.isnull()] = ''

# Extract article links through google searches
doc_identifier = df_content.doc_full_name + ' ' + df_content.doc_description

def extract_link(text):
	try:
		link = list(search(text, tld="com", num=2, stop=2))[0]
	except:
		link = "{{ url_for('notfound') }}"
	return link

df_content['link'] = doc_identifier.progress_apply(extract_link)
# <----- CLEAN DATA [finished] ----->

# Merge data-sets on article id
df_merged = df.drop('title', axis=1).merge(df_content[['article_id', 'doc_full_name', 'doc_description', 'link']], on='article_id', how='outer')

# Save data to database
engine = create_engine('sqlite:///data/data.db')
df_merged.to_sql('user-article-interactions', engine, index=False, if_exists='replace')