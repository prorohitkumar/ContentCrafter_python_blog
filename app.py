import markdown
from flask import Flask, request, jsonify, send_file
import json
import os
import google.generativeai as genai
from flask_cors import CORS
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import aspose.words as aw
from Markdown2docx import Markdown2docx
import httplib2
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run_flow
from googleapiclient import discovery

# Initializing the App and Gemini API: We initialize our Flask app and load the Gemini API client.
working_dir = os.path.dirname(os.path.abspath(__file__))

# path of config_data file
config_file_path = f"{working_dir}/config.json"
config_data = json.load(open("config.json"))

# loading the GOOGLE_API_KEY
GOOGLE_API_KEY = config_data["GOOGLE_API_KEY"]

# configuring google.generativeai with API key
genai.configure(api_key=GOOGLE_API_KEY)

app = Flask(__name__)
app.debug = True

CORS(app)
config = {
    'temperature': 0,
    'top_k': 20,
    'top_p': 0.9,
    'max_output_tokens': 2048
}

model = genai.GenerativeModel(model_name="gemini-pro")




input_text = ""
# Defining Routes: We define two routes - one for the home page and another for handling chat messages.
@app.route('/', methods=['GET'])
def hello_world():
    return "Hii"


@app.route('/blog', methods=['POST'])
def blog():
    global input_text
    input_text = request.form['input_text']
    no_words = request.form['no_words']
    blog_style = request.form['blog_style']
    keywords = request.form['keywords']
    prompt = f"""Act as a blog post writer. You need to write a blog post on {input_text} with some hashtags 
    incorporating these {keywords}.Ensure that the blog post is of around {no_words} words.
    The blog post should address blog {blog_style} level readers.
    Make sure not to mention number of words counting in response."""

    response = model.generate_content(prompt, safety_settings={
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    })

    generated_blog = response.parts[0].text
    return generated_blog


@app.route('/blogPost', methods=['POST'])
def postToBlog():
    credentials = authorize_credentials()
    http = credentials.authorize(httplib2.Http())
    discoveryUrl = 'https://blogger.googleapis.com/$discovery/rest?version=v3'
    service = discovery.build('blogger', 'v3', http=http, discoveryServiceUrl=discoveryUrl)
    content = markdown.markdown(blog())
    payload = {
        "content": content,
        "title": input_text
    }
    try:
        insert = service.posts().insert(blogId='866940012323373450', body=payload).execute()

        return insert
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})
def authorize_credentials():
    CLIENT_SECRET = 'credentials.json'
    SCOPE = 'https://www.googleapis.com/auth/blogger'
    STORAGE = Storage('creds.storage')
    # Fetch credentials from storage
    credentials = STORAGE.get()
    # If the credentials doesn't exist in the storage location then run the flow
    if credentials is None or credentials.invalid:
        flow = flow_from_clientsecrets(CLIENT_SECRET, scope=SCOPE)
        http = httplib2.Http()
        credentials = run_flow(flow, STORAGE, http=http)
    return credentials



if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5001)
