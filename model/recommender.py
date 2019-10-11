# Import data management libraries
import numpy as np
import pandas as pd

# Import Natural Language Processing Libraries
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize, sent_tokenize
nltk.download(['stopwords', 'punkt', 'averaged_perceptron_tagger', 'wordnet'], quiet=True)
import re

# Import Machine Learning libraries
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer

# Import OS and pickling libraries
import cloudpickle
import os

# Get current path
dir_path = os.path.dirname(os.path.realpath(__file__))

# Create collaborative filtering class
class Collaborative:
    """
    User-user collaborative filtering recommender system

    Attributes:
        df (pandas dataframe): user-article interaction data with user id,
            article id, title, description and link
        user_id (int): integer identifier for users

    Methods:
        get_user_by_item : generate a user-by-item matrix
        get_top_similar_users: for a user, get users with highest cosine similarity with user
        get_most_viewed_articles: sort a user's article database by the popularity of articles
        make_collaborative_recs: get the most popular articles from the most similar users

    """
    def __init__(self, df, user_id):
        self.df = df.dropna(subset=['user_id']).reset_index(drop=True)
        self.user_id = user_id

    def get_user_by_item(self):
        """Function to generate user-item matrix

        Args:
            None

        Returns:
            pandas dataframe where 1 indicates article is read and 0 that it is not
        """
        self.df['ones'] = 1
        user_item_matrix = self.df.groupby(['user_id', 'article_id']).mean().ones.unstack(level=1)
        user_item_matrix[user_item_matrix.isnull()] = 0.0
        return user_item_matrix

    def get_top_similar_users(self):
        """Function to find users with highest cosine similarity to a particular user

        Args:
            None

        Returns:
            similar users sorted by the level of cosine similarity
        """
        user_by_article = self.get_user_by_item()
        similarity = user_by_article.drop(self.user_id, axis=0).apply(lambda x: np.dot(x, user_by_article.loc[self.user_id]), axis=1)
        return similarity.sort_values(ascending=False).index.tolist()

    def get_most_viewed_articles(self, user_id):
        """Function to sort user read articles by overall popularity among all users

        Args:
            user_id (int): integer identifier for users

        Returns:
            sorted list of user read articles
        """
        article_counts = self.df.article_id[self.df.user_id == user_id].value_counts()
        return article_counts.sort_values(ascending=False).index.tolist()

    def make_collaborative_recs(self, n_rec = 30):
        """Function to get the most popular articles from the most similar users

        Args:
            n_rec (int): number of recommendations to make

        Returns:
              list of (title, description, link) tuples of recommended articles
        """
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
        article_titles = self.df.doc_full_name[self.df.article_id.isin(recommendations)].unique().tolist()
        #article_descriptions = df.doc_description[df.article_id.isin(recommendations)].unique().tolist()
        links = dict()
        descr = dict()
        for title in article_titles:
            links[title] = self.df.link[self.df.doc_full_name==title].tolist()[0]
            descr[title] = self.df.doc_description[self.df.doc_full_name==title].tolist()[0]
        article_links = links.values()
        article_descriptions = descr.values()
        #article_links = df.link[df.article_id.isin(recommendations)].unique().tolist()
        return zip(article_titles, article_descriptions, article_links)

# Make content based recommender system
class Content:
    """
    Content based recommender system to make article recommendations

    Attributes:
        df (pandas dataframe): user-article interaction data with user id,
            article id, title, description and link
        user_articles (list): list of user read articles
        articles (list): list of recently read articles

    Methods:
         tokenize: get tokenized version of some text
         get_bag_of_words: generate a normalized bag of words matrix using all words across all documents
         make_content_recs: get articles most similar to recently read articles
    """
    def __init__(self, df, user_id, articles):
        self.user_articles = df.doc_full_name[df.user_id==user_id].unique().tolist()
        self.df = df[['doc_full_name', 'doc_description', 'link']].drop_duplicates(keep='first').reset_index(drop=True)
        self.articles = articles

    def tokenize(self, text):
        '''Function to tokenize some text

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
        '''Function to generate a bag of words matrix

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

        df_text = self.df.copy(deep=True)
        df_text[df_text.isnull()] = ''
        article_text = (df_text.doc_description + ' ' + df_text.doc_full_name).values
        text_transformed = pipeline.fit_transform(article_text)
        return text_transformed.todense()

    def make_content_recs(self, m=30):
        """Function to find articles with most similarity in content to already read articles

        Args:
            m (int): number of recommendations to make

        Returns:
            list of (title, description, links) tuples of recommended articles
        """
        try:
            similarity_mat = cloudpickle.load(open(os.path.join(dir_path, 'content_similarity'), "rb"))
        except:
            indicator_mat = self.get_bag_of_words()
            similarity_mat = np.dot(indicator_mat, indicator_mat.T)
            cloudpickle.dump(similarity_mat, open(os.path.join(dir_path, 'content_similarity'), "wb"))
            similarity_mat = cloudpickle.load(open(os.path.join(dir_path, 'content_similarity'), "rb"))

        user_article_rows = self.df[self.df.doc_full_name.isin(self.user_articles)].index

        recommendations = []
        for article_row in user_article_rows:
            similar_content_article_rows = np.where(similarity_mat[article_row] >= np.percentile(similarity_mat[article_row], 99))[1]
            articles = self.df.iloc[similar_content_article_rows].doc_full_name
            for article in articles:
                if article not in recommendations and article not in self.user_articles:
                    if len(recommendations) < m:
                        recommendations.append(article)
                if len(recommendations) >= m:
                    break
            if len(recommendations) >= m:
                break
        article_titles = recommendations
        links = dict()
        descr = dict()
        for title in article_titles:
            links[title] = self.df.link[self.df.doc_full_name == title].tolist()[0]
            descr[title] = self.df.doc_description[self.df.doc_full_name == title].tolist()[0]
        article_links = links.values()
        article_descriptions = descr.values()
        # article_links = df.link[df.article_id.isin(recommendations)].unique().tolist()
        return zip(article_titles, article_descriptions, article_links)

# Get most popular articles for new users
def get_top_ranked_articles(df, n=30):
    """Get the most popular articles regardless of user preferences

    Args:
        n (int): number of top articles to get

    Returns:
          list of (title, description, links) tuples of most popular articles
    """
    top_articles = df.doc_full_name.value_counts().sort_values(ascending=False).index.tolist()[:n]
    links = dict()
    descr = dict()
    for title in top_articles:
        links[title] = df.link[df.doc_full_name == title].tolist()[0]
        descr[title] = df.doc_description[df.doc_full_name == title].tolist()[0]
        if links[title]=='':
            links[title] = '#'
    top_links = links.values()
    top_descriptions = descr.values()
    return zip(top_articles, top_descriptions, top_links)