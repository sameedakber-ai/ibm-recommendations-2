import numpy as np
import pandas as pd
from sqlalchemy import create_engine
import cloudpickle

# Import NLP and ML libraries
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize, sent_tokenize
nltk.download(['stopwords', 'punkt', 'averaged_perceptron_tagger', 'wordnet'])

from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer

import re


# Read data from database table
engine = create_engine('sqlite:///data/data.db')
df = pd.read_sql_table('user-article-interactions', engine)

# Create collaborative filtering class
class Collaborative:
    def __init__(self, df, user_id):
        self.df = df.dropna()
        self.user_id = user_id

    def get_user_by_item(self):
        self.df['ones'] = 1
        user_item_matrix = self.df.groupby(['user_id', 'article_id']).mean().ones.unstack(level=1)
        user_item_matrix[user_item_matrix.isnull()] = 0.0
        return user_item_matrix

    def get_top_similar_users(self):
        user_by_article = self.get_user_by_item()
        similarity = user_by_article.drop(self.user_id, axis=0).apply(lambda x: np.dot(x, user_by_article.loc[self.user_id]), axis=1)
        return similarity.sort_values(ascending=False).index.tolist()

    def get_most_viewed_articles(self, user_id):
        article_counts = self.df.article_id[self.df.user_id == user_id].value_counts()
        return article_counts.sort_values(ascending=False).index.tolist()

    def make_collaborative_recs(self, n_rec = 10):
        similar_users = self.get_top_similar_users()
        articles_read = self.get_most_viewed_articles(self.user_id)
        recommendations = []
        for similar_user in similar_users:
            similar_user_articles = self.get_most_viewed_articles(similar_user)
            for article in similar_user_articles:
                if article not in recommendations and article not in articles_read:
                    if len(recommendations) < n_rec:
                        recommendations.append(article)
                if len(recommendations) >= n_rec:
                    break
            if len(recommendations) >= n_rec:
                break
        article_titles = df.doc_full_name[df.article_id.isin(recommendations)].unique().tolist()
        article_descriptions = df.doc_description[df.article_id.isin(recommendations)].unique().tolist()
        return article_titles, article_descriptions


class Content:
    def __init__(self, df, user_id, article_id=None):
        self.df = df[['article_id', 'doc_full_name', 'doc_description']].drop_duplicates(keep='first')
        self.user_id = user_id
        self.article_id = article_id

    def tokenize(self, text):
        '''
        INPUT:
        text - (str) raw string of some text

        OUTPUT:
        clean_tokens - (list) a list of tokenized and lemmatized words

        Description:
        Tokenizes a single string of text into list of words

        '''
        text = re.sub(r'[^a-zA-Z0-9]', ' ', text)
        tokens = word_tokenize(text)
        clean_tokens = [WordNetLemmatizer().lemmatize(w.lower()) for w in tokens if w not in stopwords.words('english')]
        return clean_tokens

    def get_bag_of_words(self):
        '''
        INPUT:
        df_content - (DataFrame) a pandas dataframe holding information about articles (id, description, title etc)

        OUTPUT:
        text_transformed - (matrix) a matrix of bag of words

        Description:
        Generates a bag of words matrix from article titles and descriptions

        '''

        pipeline = Pipeline([
            ('vect', CountVectorizer(tokenizer=self.tokenize)),
            ('trfm', TfidfTransformer())
        ])

        df_text = self.df[['doc_description', 'doc_full_name']]
        df_text[df_text.isnull()] = ''
        article_text = (df_text.doc_description + ' ' + df_text.doc_full_name).values
        text_transformed = pipeline.fit_transform(article_text)
        return text_transformed.todense()

    def get_similar_articles(self, n_recs=10):
        indicator_mat = self.get_bag_of_words()
        similarity_mat = np.dot(indicator_mat, indicator_mat.T)
        article_row = np.where(self.df.article_id == self.article_id)[0][0]
        similar_article_rows = np.where(similarity_mat[article_row] >= np.percentile(similarity_mat[article_row], 99))[1]
        similar_articles = self.df.iloc[similar_article_rows].doc_full_name.tolist()
        return similar_articles[:n_recs]