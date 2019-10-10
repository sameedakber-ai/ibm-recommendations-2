# ibm-recommendations

Analyzing user-article interactions data taken from the IBM Watson studio
to make tailored recommendations to users

## Motivation

IBM Watson Studio is home to a large set of curated articles, documents,
datasets and other resources related to the field of data science. These
resources are readily available to all users of the online platform. IBM 
requires a way to make these resources more personalized to individual
users in the form of tailored recommendations. Recommender systems are
used in commercial applications to make recommendations by predicting 
user ratings or preferences. The objective of this project is to develop
a client facing web application to query user data and to use server-side
scripting to generate tailored recommendations to clients. Application is
created in flask and sqlalchemy is used to update user-article interactions
on the webapp. Collaborative filtering (CF) and content based recommender
systems are used to make recommendations at the backend. Data is provided
by [IBM](https://dataplatform.cloud.ibm.com/home?context=wdp)

## Tech Stack

Python (scikit-learn, pandas, flask), SQL (sqlalchemy, ORM)


## Description



