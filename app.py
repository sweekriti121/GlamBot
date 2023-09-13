from gensim.models import Word2Vec
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
import os
from dotenv import load_dotenv
import openai
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import string
from flask import Flask, request, jsonify,render_template
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

load_dotenv()
api_key = os.getenv("API_KEY")
openai.api_key = api_key

data = pd.read_csv('Myntra Fasion Clothing.csv')
urls = data['URL'].tolist()

def preprocess_text(text):
    # Convert to lowercase
    text = text.lower()
    # Remove punctuation
    text = text.translate(str.maketrans('', '', string.punctuation))
    # Tokenize the text
    tokens = word_tokenize(text)
    # Remove stopwords
    tokens = [word for word in tokens if word not in stopwords.words('english')]
    # Join tokens back to a clean text
    cleaned_text = ' '.join(tokens)
    return cleaned_text

def get_description_vector(description):
    vector = sum([word2vec_model.wv[word] for word in description.split() if word in word2vec_model.wv])
    return vector

word2vec_model = Word2Vec.load("word2vec_model.model")

# Load the cleaned descriptions and description vectors
with open("cleaned_descriptions.txt", "r") as f:
    cleaned_descriptions = [line.strip() for line in f.readlines()]

description_vectors = np.load("description_vectors.npy")
user_query = "green dress"
user_query_cleaned = preprocess_text(user_query)
user_query_vector = get_description_vector(user_query_cleaned)
user_query_vector = np.array([user_query_vector])
similarities = cosine_similarity(user_query_vector, description_vectors)
similarities = similarities.flatten()
top_indices = similarities.argsort()[-5:][::-1]
top_item_links = [urls[i] for i in top_indices]

prompt = '''you will act as chatbot for my backend api. make sure your responses are
            in normal understandable way such that i can use it as a parameter in my model,
            always try to generate recommendation as close as modern indian culture to generate the best possible response.
            categories to consider: tshirts, sarees, tops,kurtas,
            dresses, shirts,kurta,jeans,trousers,bra,shorts,sweatshirts,jackets,
            briefs,sweaters,nightdress,leggings,skirts,palazzos,tights,socks,dupatta,trunk,jumpsuit,boxers,
            blazers,capris,saree-blouse,shrug,lingerie-set,dhotis,tracksuits,jeggings,sherwani,swimwear,
            
            '''
openai_response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
        {"role": "user", "content": prompt}
        ],
        max_tokens=50,
        stop=None,
        temperature=0.2,
    )

print(openai_response)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_response', methods=['POST'])
def get_response():
    user_message = request.json['user_message']
    
    # Use OpenAI to generate outfit recommendations
    augmented_message = f"{user_message} - Generate 2 three word(not more than 3 words) outfit recommendations all separated by new line escape sequence considering the occasion and age, with 1st word being the color and 2nd being the category of outfit(all given in previous text) and 3rd being gender(men/women) in this format : color category gender \n color category gender " 
    openai_response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
        {"role": "user", "content": augmented_message}
        ],
        max_tokens=50,
        stop=None,
        temperature=0.1,
    )
    print(openai_response)
    response_data = openai_response.choices[0].message

# Extract the outfit recommendations and split them by newline
    outfit_recommendations = response_data['content'].strip().split('\n')

# Filter and extract three-word outfits
    three_word_outfits = [outfit.strip() for outfit in outfit_recommendations if len(outfit.split()) >= 3]
    print(three_word_outfits)
    # Generate links for each outfit recommendation
    response_data = []
    for outfit in three_word_outfits:
        user_query_cleaned = preprocess_text(outfit)
        user_query_vector = get_description_vector(user_query_cleaned)
        user_query_vector = np.array([user_query_vector])
        similarities = cosine_similarity(user_query_vector, description_vectors)
        top_indices = similarities[0].argsort()[-3:][::-1]
        top_item_links = [urls[i] for i in top_indices]  
        response_data.append({"outfit": outfit, "similar_links": top_item_links})
    return jsonify({"outfit_recommendations": response_data[:2]})  



if __name__ == '__main__':
    app.run(debug=True)