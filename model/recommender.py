import numpy as np
import pandas as pd
from sqlalchemy import create_engine

# Read data from database
engine = create_engine('sqlite:///data/data.db')
df = pd.read_sql_table('user-article-interactions', engine)

# Create collaborative filtering class
class Collaborative:
    def __init__(self, df, user_id):
        self.df = df
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
        return article_titles


